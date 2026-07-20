"""
Dataset ingestion service with idempotent ingestion.

Provides a registry of available datasets and ensures each dataset
is only ingested once by tracking state in MongoDB.
"""

import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.database.collections import get_dataset_ingestion_collection
from app.services.knowledge_service import knowledge_service

# Ensure scripts package is importable for loaders.
_BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))


# ---------------------------------------------------------------------------
# Dataset registry
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DatasetDefinition:
    """Metadata for one ingestible dataset."""

    name: str
    """Unique identifier, e.g. ``"faq"``."""

    display_name: str
    """Human-readable name shown in the UI."""

    description: str
    """Short description of what this dataset contains."""

    loader_name: str
    """Name of the loader function in ``scripts.loaders``."""

    source_tag: str
    """Value stored in the ``source`` field of ingested documents."""

    path: str | None
    """Relative path from the backend root, or ``None`` for remote datasets."""

    category: str
    """Default category for all documents in this dataset."""

    needs_path: bool = True
    """Whether the loader requires a file path."""

    sample_limit: int | None = None
    """Optional default sample limit to avoid ingesting extremely large datasets."""


DATASET_REGISTRY: list[DatasetDefinition] = [
    DatasetDefinition(
        name="faq",
        display_name="FAQ — Sample Questions & Answers",
        description=(
            "3 frequently asked questions covering password "
            "resets, refunds, and subscriptions."
        ),
        loader_name="FaqLoader",
        source_tag="sample_faq",
        path="datasets/sample_faq.json",
        category="faq",
    ),
    DatasetDefinition(
        name="banking77",
        display_name="Banking77 — Customer Intent Queries",
        description=(
            "13,083 customer service queries labeled with 77 "
            "fine-grained banking intents from PolyAI."
        ),
        loader_name="Banking77Loader",
        source_tag="banking77",
        path=None,
        category="banking",
        needs_path=False,
    ),
    DatasetDefinition(
        name="squad",
        display_name="SQuAD — Reading Comprehension Passages",
        description=(
            "Wikipedia articles with question-answer pairs "
            "for general knowledge retrieval."
        ),
        loader_name="SquadLoader",
        source_tag="squad_v1.1",
        path=("datasets/SQuAD-explorer/dataset/dev-v1.1.json"),
        category="general_knowledge",
        sample_limit=50,
    ),
    DatasetDefinition(
        name="dailydialog",
        display_name="DailyDialog — Multi-Turn Conversations",
        description=(
            "Open-domain dialogue snippets for " "conversational context training."
        ),
        loader_name="DailyDialogLoader",
        source_tag="xdailydialog_en",
        path=("datasets/XDailyDialog/data/" "1k_part_data/dialogues_text_En.txt"),
        category="conversation",
        sample_limit=200,
    ),
    DatasetDefinition(
        name="complaints",
        display_name="CFPB Consumer Complaints",
        description=(
            "Consumer financial complaint narratives from "
            "the Consumer Financial Protection Bureau."
        ),
        loader_name="ComplaintsLoader",
        source_tag="complaints",
        path="datasets/complaints.json.zip",
        category="complaints",
        sample_limit=500,
    ),
]

_REGISTRY_BY_NAME: dict[str, DatasetDefinition] = {
    ds.name: ds for ds in DATASET_REGISTRY
}


# ---------------------------------------------------------------------------
# Response types
# ---------------------------------------------------------------------------


@dataclass
class DatasetStatus:
    """A dataset's ingestion status for API responses."""

    name: str
    display_name: str
    description: str
    source: str
    is_ingested: bool
    document_count: int
    chunk_count: int
    ingested_at: str | None


@dataclass
class IngestionResult:
    """Result of an ingestion run."""

    ingested: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    failed: list[tuple[str, str]] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class DatasetService:
    """Manages dataset ingestion with idempotency tracking."""

    # -- Loader dispatch ---------------------------------------------------

    @staticmethod
    def _load_dataset(definition: DatasetDefinition) -> list[Any]:
        """Load documents using the appropriate loader."""

        # Lazy import to avoid circular dependencies and heavy imports at
        # module load time.
        from scripts.loaders import (
            Banking77Loader,
            ComplaintsLoader,
            DailyDialogLoader,
            FaqLoader,
            SquadLoader,
        )

        LOADER_MAP = {
            "FaqLoader": FaqLoader,
            "Banking77Loader": Banking77Loader,
            "SquadLoader": SquadLoader,
            "DailyDialogLoader": DailyDialogLoader,
            "ComplaintsLoader": ComplaintsLoader,
        }

        loader_cls = LOADER_MAP.get(definition.loader_name)
        if loader_cls is None:
            raise ValueError(f"Unknown loader: {definition.loader_name}")

        kwargs: dict[str, Any] = {}
        if definition.needs_path and definition.path is not None:
            full_path = _BACKEND_ROOT / definition.path
            if not full_path.exists():
                raise FileNotFoundError(f"Dataset file not found: {full_path}")
            kwargs["path"] = str(full_path)

        if definition.sample_limit is not None:
            kwargs["sample"] = definition.sample_limit

        return loader_cls(**kwargs)  # type: ignore[call-arg]

    # -- Idempotency checks ------------------------------------------------

    @staticmethod
    async def _is_ingested(dataset_name: str, user_id: str) -> bool:
        """Check if a dataset has already been successfully ingested."""

        collection = get_dataset_ingestion_collection()
        doc = await collection.find_one(
            {
                "dataset_name": dataset_name,
                "user_id": user_id,
                "status": "completed",
            }
        )
        return doc is not None

    @staticmethod
    async def _log_ingestion(
        dataset_name: str,
        user_id: str,
        *,
        status: str,
        document_count: int = 0,
        chunk_count: int = 0,
    ) -> None:
        """Write or update an ingestion log entry."""

        collection = get_dataset_ingestion_collection()
        now = datetime.now(UTC)

        await collection.update_one(
            {"dataset_name": dataset_name, "user_id": user_id},
            {
                "$set": {
                    "status": status,
                    "document_count": document_count,
                    "chunk_count": chunk_count,
                    "ingested_at": now,
                    "updated_at": now,
                },
                "$setOnInsert": {
                    "dataset_name": dataset_name,
                    "user_id": user_id,
                    "created_at": now,
                },
            },
            upsert=True,
        )

    # -- Public API --------------------------------------------------------

    async def get_available_datasets(self, user_id: str) -> list[DatasetStatus]:
        """Return all registered datasets with their ingestion status."""

        collection = get_dataset_ingestion_collection()
        cursor = collection.find({"user_id": user_id})
        logs = {doc["dataset_name"]: doc async for doc in cursor}

        result: list[DatasetStatus] = []
        for definition in DATASET_REGISTRY:
            log = logs.get(definition.name)
            is_done = log is not None and log.get("status") == "completed"

            result.append(
                DatasetStatus(
                    name=definition.name,
                    display_name=definition.display_name,
                    description=definition.description,
                    source=definition.source_tag,
                    is_ingested=is_done,
                    document_count=log.get("document_count", 0) if log else 0,
                    chunk_count=log.get("chunk_count", 0) if log else 0,
                    ingested_at=(
                        log["ingested_at"].isoformat()
                        if log and log.get("ingested_at")
                        else None
                    ),
                )
            )

        return result

    async def ingest_dataset(
        self,
        dataset_name: str,
        user_id: str,
        *,
        force: bool = False,
    ) -> tuple[bool, str]:
        """
        Ingest a single dataset. Returns (success, message).

        Skips if already ingested unless ``force=True``.
        """

        definition = _REGISTRY_BY_NAME.get(dataset_name)
        if definition is None:
            return False, f"Unknown dataset: {dataset_name}"

        if not force and await self._is_ingested(dataset_name, user_id):
            return True, f"Dataset '{dataset_name}' already ingested — skipping."

        try:
            await self._log_ingestion(dataset_name, user_id, status="ingesting")

            documents = self._load_dataset(definition)
            if not documents:
                await self._log_ingestion(dataset_name, user_id, status="completed")
                return (
                    True,
                    f"Dataset '{dataset_name}' loaded 0 documents — nothing to ingest.",
                )

            total_chunks = 0
            success_count = 0

            for doc in documents:
                try:
                    response = await knowledge_service.ingest_text(
                        user_id=user_id,
                        title=doc.title,
                        category=doc.category,
                        source=definition.source_tag,
                        text=doc.text,
                    )
                    total_chunks += response.chunk_count
                    success_count += 1
                except Exception:
                    # Individual document failures are logged but don't stop
                    # the rest of the dataset.
                    pass

            await self._log_ingestion(
                dataset_name,
                user_id,
                status="completed",
                document_count=success_count,
                chunk_count=total_chunks,
            )

            return True, (
                f"Dataset '{dataset_name}' ingested: "
                f"{success_count}/{len(documents)} documents, "
                f"{total_chunks} chunks."
            )

        except Exception as exc:
            await self._log_ingestion(dataset_name, user_id, status="failed")
            return False, f"Dataset '{dataset_name}' failed: {exc}"

    async def ingest_all_datasets(
        self,
        user_id: str,
        *,
        force: bool = False,
    ) -> IngestionResult:
        """Ingest all registered datasets, skipping already-ingested ones."""

        result = IngestionResult()

        for definition in DATASET_REGISTRY:
            if not force and await self._is_ingested(definition.name, user_id):
                result.skipped.append(definition.name)
                continue

            success, message = await self.ingest_dataset(
                definition.name, user_id, force=force
            )

            if success:
                result.ingested.append(definition.name)
            else:
                result.failed.append((definition.name, message))

        return result


dataset_service = DatasetService()

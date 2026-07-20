import json
from pathlib import Path
from typing import TypedDict

import faiss
import numpy as np

from app.core.config import settings
from app.schemas.retrieval import VectorSearchResult
from app.services.embedding_service import embedding_service


class VectorReference(TypedDict):
    """Identifiers that locate the canonical text for one indexed vector."""

    document_id: str
    chunk_id: str


class VectorMappingReindexRequiredError(RuntimeError):
    """Raised when persisted vector references cannot locate canonical chunks."""


class VectorService:
    """
    Handles FAISS vector indexing and similarity search.
    """

    def __init__(
        self,
        storage_path: Path | None = None,
    ) -> None:

        self.storage_path = (
            storage_path
            if storage_path is not None
            else Path(settings.FAISS_INDEX_PATH)
        )
        self.storage_path.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.index_file = self.storage_path / settings.FAISS_INDEX_NAME

        self.mapping_file = self.storage_path / settings.FAISS_MAPPING_NAME

        self.dimension = embedding_service.dimension()

        self.index = faiss.IndexFlatIP(self.dimension)

        self.mapping: list[VectorReference] = []

        self.load()

    def add(
        self,
        vector_references: list[VectorReference],
        embeddings: np.ndarray,
    ) -> None:

        if len(vector_references) == 0:
            return
        if embeddings.size == 0:
            return
        if len(vector_references) != len(embeddings):
            raise ValueError(
                "Vector references and embeddings must have equal lengths."
            )

        validated_references = [
            self._validate_reference(reference) for reference in vector_references
        ]

        self.index.add(embeddings)

        self.mapping.extend(validated_references)

    def search(
        self,
        query_embedding: np.ndarray,
        k: int | None = None,
    ) -> list[VectorSearchResult]:

        if self.index.ntotal == 0:
            return []

        if query_embedding.ndim == 1:
            query_embedding = np.expand_dims(
                query_embedding,
                axis=0,
            )

        k = min(
            k or settings.TOP_K_RESULTS,
            self.index.ntotal,
        )

        scores, indices = self.index.search(
            query_embedding,
            k,
        )

        results = []

        for score, idx in zip(
            scores[0],
            indices[0],
        ):

            if idx == -1:
                continue

            vector_reference = self.mapping[idx]

            results.append(
                VectorSearchResult(
                    document_id=vector_reference["document_id"],
                    chunk_id=vector_reference["chunk_id"],
                    score=float(score),
                )
            )

        return results

    def save(self) -> None:

        faiss.write_index(
            self.index,
            str(self.index_file),
        )

        with open(
            self.mapping_file,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                self.mapping,
                file,
                indent=2,
            )

    def load(self) -> None:
        if self.index_file.exists():
            self.index = faiss.read_index(str(self.index_file))

        if not self.mapping_file.exists():
            if self.index.ntotal:
                raise VectorMappingReindexRequiredError(
                    "FAISS mapping is missing; reindex required."
                )
            return

        with open(
            self.mapping_file,
            encoding="utf-8",
        ) as file:
            mapping = json.load(file)

        if not isinstance(mapping, list) or any(
            not isinstance(reference, dict) for reference in mapping
        ):
            raise VectorMappingReindexRequiredError(
                "Legacy FAISS mapping lacks document_id; reindex required."
            )

        self.mapping = [self._validate_reference(reference) for reference in mapping]

        if len(self.mapping) != self.index.ntotal:
            raise VectorMappingReindexRequiredError(
                "FAISS index and mapping are out of sync; reindex required."
            )

    def rebuild(
        self,
        vector_references: list[VectorReference],
        embeddings: np.ndarray,
    ) -> None:

        self.index = faiss.IndexFlatIP(self.dimension)

        self.mapping = []

        self.add(
            vector_references,
            embeddings,
        )

        self.save()

    def remove_document(self, document_id: str) -> int:
        """Remove all vectors belonging to a document. Returns count removed."""

        indices_to_keep = [
            i for i, ref in enumerate(self.mapping) if ref["document_id"] != document_id
        ]

        if len(indices_to_keep) == self.index.ntotal:
            return 0

        removed = self.index.ntotal - len(indices_to_keep)

        if indices_to_keep:
            all_vectors = self.index.reconstruct_n(0, self.index.ntotal)
            remaining = all_vectors[indices_to_keep]
            rebuilt = faiss.IndexFlatIP(self.dimension)
            rebuilt.add(remaining)
            self.index = rebuilt
        else:
            self.index = faiss.IndexFlatIP(self.dimension)

        self.mapping = [self.mapping[i] for i in indices_to_keep]
        self.save()

        return removed

    def _validate_reference(self, reference: object) -> VectorReference:
        """Validate identifiers required to resolve an indexed canonical chunk."""

        if not isinstance(reference, dict):
            raise VectorMappingReindexRequiredError(
                "Legacy vector reference lacks document_id; reindex required."
            )

        document_id = reference.get("document_id")
        chunk_id = reference.get("chunk_id")

        if (
            not isinstance(document_id, str)
            or not document_id
            or not isinstance(chunk_id, str)
            or not chunk_id
        ):
            raise VectorMappingReindexRequiredError(
                "FAISS mapping lacks document_id or chunk_id; reindex required."
            )

        return {
            "document_id": document_id,
            "chunk_id": chunk_id,
        }


class LazyVectorService:
    """Delay FAISS/model initialization until a retrieval operation needs it."""

    def __init__(self) -> None:
        self._instance: VectorService | None = None

    @property
    def instance(self) -> VectorService:
        if self._instance is None:
            self._instance = VectorService()
        return self._instance

    def search(
        self, query_embedding: np.ndarray, k: int | None = None
    ) -> list[VectorSearchResult]:
        return self.instance.search(query_embedding, k)


vector_service = LazyVectorService()

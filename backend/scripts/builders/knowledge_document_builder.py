"""Orchestrates dataset ingestion by calling the backend's KnowledgeService."""

import time
from collections.abc import Callable, Iterable

from app.services.knowledge_service import knowledge_service
from scripts.loaders.base import DocumentInput


class IngestionResult:
    """Summary of one document's ingestion attempt."""

    def __init__(self) -> None:
        self.successful: list[str] = []
        self.failed: list[tuple[str, str]] = []  # (title, reason)

    @property
    def total(self) -> int:
        return len(self.successful) + len(self.failed)


async def ingest_documents(
    documents: Iterable[DocumentInput],
    *,
    user_id: str,
    progress_callback: Callable | None = None,
) -> IngestionResult:
    """Ingest a stream of documents through KnowledgeService.

    Each document is ingested independently so a single failure does not
    block the rest.  The failed document's partial state is rolled back by
    ``knowledge_service.ingest_text``.
    """
    result = IngestionResult()
    total_chunks = 0
    start_time = time.monotonic()

    for doc in documents:
        try:
            response = await knowledge_service.ingest_text(
                user_id=user_id,
                title=doc.title,
                category=doc.category,
                source=doc.source,
                text=doc.text,
            )
            result.successful.append(doc.title)
            total_chunks += response.chunk_count
        except Exception as exc:  # noqa: BLE001
            result.failed.append((doc.title, str(exc)))

        if progress_callback is not None:
            progress_callback(result, total_chunks, start_time)

    return result


def format_summary(result: IngestionResult, total_chunks: int) -> str:
    """Return a human-readable ingestion summary."""
    lines = [
        "── Ingestion Summary ──",
        f"  Successful:  {len(result.successful)}",
        f"  Failed:      {len(result.failed)}",
        f"  Total chunks: {total_chunks}",
    ]

    if result.failed:
        lines.append("")
        lines.append("  Failed documents:")
        for title, reason in result.failed:
            lines.append(f"    - {title}: {reason}")

    return "\n".join(lines)

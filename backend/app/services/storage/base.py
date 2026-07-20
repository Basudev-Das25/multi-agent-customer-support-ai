"""Contracts and data structures for persisted knowledge chunks."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, runtime_checkable


class ChunkStorageError(Exception):
    """Base exception raised by chunk storage implementations."""


class ChunkStorageValidationError(ChunkStorageError):
    """Raised when chunk data does not satisfy storage invariants."""


class ChunkStorageCorruptionError(ChunkStorageError):
    """Raised when persisted chunk data cannot be trusted."""


class ChunkStorageWriteError(ChunkStorageError):
    """Raised when a chunk snapshot cannot be written safely."""


@dataclass(frozen=True, slots=True)
class StoredChunk:
    """Canonical, globally shared knowledge chunk stored by a chunk backend."""

    document_id: str
    page_number: int
    chunk_index: int
    text: str
    created_at: datetime
    id: str | None = None
    text_sha256: str | None = None


@runtime_checkable
class ChunkStorage(Protocol):
    """Asynchronous interface for document-scoped chunk text storage."""

    async def save_chunks(self, *, chunks: Sequence[StoredChunk]) -> list[StoredChunk]:
        """Atomically replace the complete chunk snapshot for one document."""

    async def load_chunks(self, *, document_id: str) -> list[StoredChunk]:
        """Load every chunk stored for a document in document order."""

    async def get_chunk(
        self,
        *,
        document_id: str,
        chunk_id: str,
    ) -> StoredChunk | None:
        """Return one chunk from a document when it exists."""

    async def get_chunks(
        self,
        *,
        document_id: str,
        chunk_ids: Sequence[str],
    ) -> list[StoredChunk]:
        """Return existing chunks in the caller-provided identifier order."""

    async def delete_document(self, *, document_id: str) -> bool:
        """Remove all chunks for a document. Return True when data was removed."""

    async def get_chunk_window(
        self,
        *,
        document_id: str,
        chunk_id: str,
        before: int = 1,
        after: int = 1,
    ) -> list[StoredChunk]:
        """Return a target chunk and its adjacent document neighbours."""

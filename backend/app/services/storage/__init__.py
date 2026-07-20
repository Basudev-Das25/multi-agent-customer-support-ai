"""Storage abstractions for locally persisted knowledge artifacts."""

from app.services.storage.base import (
    ChunkStorage,
    ChunkStorageCorruptionError,
    ChunkStorageError,
    ChunkStorageValidationError,
    ChunkStorageWriteError,
    StoredChunk,
)
from app.services.storage.local_chunk_storage import LocalChunkStorage

__all__ = [
    "ChunkStorage",
    "ChunkStorageCorruptionError",
    "ChunkStorageError",
    "ChunkStorageValidationError",
    "ChunkStorageWriteError",
    "LocalChunkStorage",
    "StoredChunk",
]

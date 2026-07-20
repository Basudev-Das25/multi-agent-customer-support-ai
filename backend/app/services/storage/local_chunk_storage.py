"""Local JSONL implementation of the document-scoped chunk storage contract."""

import asyncio
import errno
import hashlib
import json
import os
import re
import shutil
import time
from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import BinaryIO
from uuid import NAMESPACE_URL, uuid4, uuid5

from app.services.storage.base import (
    ChunkStorage,
    ChunkStorageCorruptionError,
    ChunkStorageValidationError,
    ChunkStorageWriteError,
    StoredChunk,
)


@dataclass(frozen=True, slots=True)
class _CachedDocument:
    """Parsed immutable representation of one stored document generation."""

    generation: str
    chunks_by_id: dict[str, StoredChunk]
    chunk_ids_by_index: tuple[str, ...]
    chunk_index_by_id: dict[str, int]


class LocalChunkStorage(ChunkStorage):
    """Store globally shared document chunks in local JSONL snapshots.

    Each document is cached after its first read. A manifest generation check keeps
    caches coherent when another process successfully replaces a document snapshot.
    """

    _SCHEMA_VERSION = 1
    _LOCK_TIMEOUT_SECONDS = 10.0
    _LOCK_RETRY_SECONDS = 0.05

    def __init__(self, storage_path: Path | None = None) -> None:
        """Initialize storage rooted at the approved local documents directory."""

        self.storage_path = storage_path or Path("storage/knowledge/documents")
        self._cache: dict[str, _CachedDocument] = {}
        self._document_locks: dict[str, asyncio.Lock] = {}

    async def save_chunks(self, *, chunks: Sequence[StoredChunk]) -> list[StoredChunk]:
        """Atomically replace the complete chunk snapshot for one document."""

        canonical_chunks = self._canonicalize_chunks(chunks)
        document_id = canonical_chunks[0].document_id

        await asyncio.to_thread(self.storage_path.mkdir, parents=True, exist_ok=True)

        async with self._locked_document(document_id):
            generation = str(uuid4())
            document_path = self._document_path(document_id)
            await asyncio.to_thread(document_path.mkdir, parents=True, exist_ok=True)

            try:
                jsonl_bytes = self._serialize_chunks(canonical_chunks)
                chunk_offset = await asyncio.to_thread(
                    self._prepare_chunks_for_append,
                    document_path,
                )
                manifest_bytes = self._serialize_manifest(
                    document_id=document_id,
                    chunks=canonical_chunks,
                    generation=generation,
                    content_sha256=self._sha256(jsonl_bytes),
                    chunk_offset=chunk_offset,
                    chunk_length=len(jsonl_bytes),
                )
                await asyncio.to_thread(
                    self._replace_snapshot,
                    document_path,
                    jsonl_bytes,
                    manifest_bytes,
                )
            except OSError as exc:
                raise ChunkStorageWriteError(
                    f"Could not write chunk storage for document '{document_id}'."
                ) from exc

            self._cache.pop(document_id, None)

        return canonical_chunks

    async def load_chunks(self, *, document_id: str) -> list[StoredChunk]:
        """Load every chunk stored for a document in document order."""

        cached_document = await self._load_document(document_id)
        if cached_document is None:
            return []

        return [
            cached_document.chunks_by_id[chunk_id]
            for chunk_id in cached_document.chunk_ids_by_index
        ]

    async def get_chunk(
        self,
        *,
        document_id: str,
        chunk_id: str,
    ) -> StoredChunk | None:
        """Return one chunk from a document when it exists."""

        cached_document = await self._load_document(document_id)
        if cached_document is None:
            return None

        return cached_document.chunks_by_id.get(chunk_id)

    async def get_chunks(
        self,
        *,
        document_id: str,
        chunk_ids: Sequence[str],
    ) -> list[StoredChunk]:
        """Return existing chunks in the caller-provided identifier order."""

        cached_document = await self._load_document(document_id)
        if cached_document is None:
            return []

        return [
            cached_document.chunks_by_id[chunk_id]
            for chunk_id in chunk_ids
            if chunk_id in cached_document.chunks_by_id
        ]

    async def get_chunk_window(
        self,
        *,
        document_id: str,
        chunk_id: str,
        before: int = 1,
        after: int = 1,
    ) -> list[StoredChunk]:
        """Return a target chunk and its adjacent document neighbours."""

        if before < 0 or after < 0:
            raise ChunkStorageValidationError(
                "Neighbour window sizes must be greater than or equal to zero."
            )

        cached_document = await self._load_document(document_id)
        if cached_document is None:
            return []

        chunk_index = cached_document.chunk_index_by_id.get(chunk_id)
        if chunk_index is None:
            return []

        start = max(0, chunk_index - before)
        end = min(len(cached_document.chunk_ids_by_index), chunk_index + after + 1)

        return [
            cached_document.chunks_by_id[neighbour_id]
            for neighbour_id in cached_document.chunk_ids_by_index[start:end]
        ]

    async def _load_document(self, document_id: str) -> _CachedDocument | None:
        """Return the current cached document generation, loading it when needed."""

        self._validate_identifier(document_id, field_name="document_id")
        manifest_path = self._manifest_path(document_id)

        if not await asyncio.to_thread(manifest_path.exists):
            self._cache.pop(document_id, None)
            return None

        manifest = await asyncio.to_thread(self._read_json, manifest_path)
        generation = self._read_manifest_generation(manifest, document_id)
        cached_document = self._cache.get(document_id)

        if cached_document is not None and cached_document.generation == generation:
            return cached_document

        async with self._locked_document(document_id):
            manifest = await asyncio.to_thread(self._read_json, manifest_path)
            generation = self._read_manifest_generation(manifest, document_id)
            cached_document = self._cache.get(document_id)

            if cached_document is not None and cached_document.generation == generation:
                return cached_document

            loaded_document = await asyncio.to_thread(
                self._read_document,
                document_id,
                manifest,
            )
            self._cache[document_id] = loaded_document
            return loaded_document

    def _canonicalize_chunks(self, chunks: Sequence[StoredChunk]) -> list[StoredChunk]:
        """Validate and normalize a complete document chunk snapshot."""

        if not chunks:
            raise ChunkStorageValidationError("At least one chunk is required.")

        document_id = chunks[0].document_id
        self._validate_identifier(document_id, field_name="document_id")

        canonical_chunks: list[StoredChunk] = []
        seen_chunk_ids: set[str] = set()

        for expected_index, chunk in enumerate(chunks):
            if chunk.document_id != document_id:
                raise ChunkStorageValidationError(
                    "All chunks in a snapshot must belong to the same document."
                )
            if chunk.chunk_index != expected_index:
                raise ChunkStorageValidationError(
                    "Chunk indexes must be contiguous and start at zero."
                )
            if chunk.page_number < 1:
                raise ChunkStorageValidationError("Page numbers must be positive.")
            if not chunk.text:
                raise ChunkStorageValidationError("Chunk text cannot be empty.")
            if chunk.created_at.tzinfo is None:
                raise ChunkStorageValidationError(
                    "Chunk creation timestamps must include a timezone."
                )

            text_sha256 = self._sha256(chunk.text.encode("utf-8"))
            if chunk.text_sha256 is not None and chunk.text_sha256 != text_sha256:
                raise ChunkStorageValidationError(
                    "Chunk text checksum does not match text."
                )

            chunk_id = chunk.id or self._build_chunk_id(chunk, text_sha256)
            self._validate_identifier(chunk_id, field_name="chunk_id")
            if chunk_id in seen_chunk_ids:
                raise ChunkStorageValidationError("Chunk identifiers must be unique.")

            seen_chunk_ids.add(chunk_id)
            canonical_chunks.append(
                StoredChunk(
                    id=chunk_id,
                    document_id=document_id,
                    page_number=chunk.page_number,
                    chunk_index=chunk.chunk_index,
                    text=chunk.text,
                    created_at=chunk.created_at.astimezone(UTC),
                    text_sha256=text_sha256,
                )
            )

        return canonical_chunks

    def _read_document(self, document_id: str, manifest: dict) -> _CachedDocument:
        """Parse and validate a document snapshot from its JSONL and manifest files."""

        jsonl_path = self._chunks_path(document_id)
        if not jsonl_path.exists():
            raise ChunkStorageCorruptionError(
                f"Chunk manifest exists but JSONL is missing for '{document_id}'."
            )

        raw_jsonl = self._read_chunk_generation(jsonl_path, manifest)
        expected_sha256 = manifest.get("content_sha256")
        if expected_sha256 != self._sha256(raw_jsonl):
            raise ChunkStorageCorruptionError(
                f"Chunk JSONL checksum does not match its manifest for '{document_id}'."
            )

        chunks: list[StoredChunk] = []
        for line_number, line in enumerate(raw_jsonl.splitlines(), start=1):
            try:
                record = json.loads(line)
                if record["schema_version"] != self._SCHEMA_VERSION:
                    raise ValueError("Unsupported chunk schema version.")
                created_at = datetime.fromisoformat(record["created_at"])
                chunk = StoredChunk(
                    id=record["id"],
                    document_id=record["document_id"],
                    page_number=record["page_number"],
                    chunk_index=record["chunk_index"],
                    text=record["text"],
                    created_at=created_at,
                    text_sha256=record["text_sha256"],
                )
            except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
                raise ChunkStorageCorruptionError(
                    f"Invalid chunk record at line {line_number} for '{document_id}'."
                ) from exc

            if chunk.document_id != document_id:
                raise ChunkStorageCorruptionError(
                    "Chunk document ID mismatch at line "
                    f"{line_number} for '{document_id}'."
                )
            if chunk.created_at.tzinfo is None:
                raise ChunkStorageCorruptionError(
                    f"Chunk timestamp is missing a timezone at line {line_number}."
                )
            if chunk.text_sha256 != self._sha256(chunk.text.encode("utf-8")):
                raise ChunkStorageCorruptionError(
                    f"Chunk text checksum mismatch at line {line_number}."
                )
            chunks.append(chunk)

        canonical_chunks = self._canonicalize_chunks(chunks)
        chunk_ids_by_index = tuple(chunk.id for chunk in canonical_chunks if chunk.id)
        manifest_ids = manifest.get("chunk_ids_by_index")
        manifest_index = manifest.get("chunk_index_by_id")

        if manifest.get("chunk_count") != len(canonical_chunks):
            raise ChunkStorageCorruptionError(
                f"Chunk count does not match JSONL for '{document_id}'."
            )
        if manifest_ids != list(chunk_ids_by_index) or not isinstance(
            manifest_index, dict
        ):
            raise ChunkStorageCorruptionError(
                f"Chunk index does not match JSONL for '{document_id}'."
            )

        expected_index = {
            chunk_id: index for index, chunk_id in enumerate(chunk_ids_by_index)
        }
        if manifest_index != expected_index:
            raise ChunkStorageCorruptionError(
                f"Chunk lookup mapping does not match JSONL for '{document_id}'."
            )

        return _CachedDocument(
            generation=self._read_manifest_generation(manifest, document_id),
            chunks_by_id={chunk.id: chunk for chunk in canonical_chunks if chunk.id},
            chunk_ids_by_index=chunk_ids_by_index,
            chunk_index_by_id=expected_index,
        )

    def _serialize_chunks(self, chunks: Sequence[StoredChunk]) -> bytes:
        """Serialize canonical chunks into a UTF-8 JSONL document."""

        records = []
        for chunk in chunks:
            records.append(
                json.dumps(
                    {
                        "schema_version": self._SCHEMA_VERSION,
                        "id": chunk.id,
                        "document_id": chunk.document_id,
                        "page_number": chunk.page_number,
                        "chunk_index": chunk.chunk_index,
                        "text": chunk.text,
                        "created_at": chunk.created_at.isoformat(),
                        "text_sha256": chunk.text_sha256,
                    },
                    ensure_ascii=False,
                    separators=(",", ":"),
                )
            )

        return ("\n".join(records) + "\n").encode("utf-8")

    def _serialize_manifest(
        self,
        *,
        document_id: str,
        chunks: Sequence[StoredChunk],
        generation: str,
        content_sha256: str,
        chunk_offset: int,
        chunk_length: int,
    ) -> bytes:
        """Serialize the derived lookup metadata for a document snapshot."""

        chunk_ids = [chunk.id for chunk in chunks if chunk.id]
        manifest = {
            "schema_version": self._SCHEMA_VERSION,
            "document_id": document_id,
            "generation": generation,
            "chunk_count": len(chunks),
            "content_sha256": content_sha256,
            "chunk_offset": chunk_offset,
            "chunk_length": chunk_length,
            "chunk_ids_by_index": chunk_ids,
            "chunk_index_by_id": {
                chunk_id: index for index, chunk_id in enumerate(chunk_ids)
            },
        }
        return json.dumps(
            manifest,
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")

    def _replace_snapshot(
        self,
        document_path: Path,
        jsonl_bytes: bytes,
        manifest_bytes: bytes,
    ) -> None:
        """Write a new durable snapshot and atomically activate its files."""

        chunks_path = document_path / "chunks.jsonl"
        self._append_durable_file(chunks_path, jsonl_bytes)
        self._replace_manifest(document_path, manifest_bytes)

    def _replace_manifest(self, document_path: Path, manifest_bytes: bytes) -> None:
        """Durably replace the manifest that activates a snapshot generation."""

        manifest_path = document_path / "manifest.json"
        manifest_temp_path = document_path / f".manifest.{uuid4().hex}.tmp"

        try:
            self._write_durable_file(manifest_temp_path, manifest_bytes)
            os.replace(manifest_temp_path, manifest_path)
            self._fsync_directory(document_path)
        finally:
            manifest_temp_path.unlink(missing_ok=True)

    def _write_durable_file(self, path: Path, contents: bytes) -> None:
        """Write, flush, and fsync one temporary storage file."""

        with path.open("wb") as file:
            file.write(contents)
            file.flush()
            os.fsync(file.fileno())

    def _append_durable_file(self, path: Path, contents: bytes) -> None:
        """Append one complete uncommitted JSONL generation and fsync it."""

        with path.open("ab") as file:
            file.write(contents)
            file.flush()
            os.fsync(file.fileno())

    def _fsync_directory(self, path: Path) -> None:
        """Persist directory metadata after atomically replacing the manifest."""

        if os.name == "nt":
            return

        directory_flags = getattr(os, "O_DIRECTORY", 0)
        descriptor = os.open(path, os.O_RDONLY | directory_flags)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)

    @asynccontextmanager
    async def _locked_document(self, document_id: str) -> AsyncIterator[None]:
        """Acquire in-process and cross-process locks for one document."""

        document_lock = self._document_locks.setdefault(document_id, asyncio.Lock())
        async with document_lock:
            lock_path = self.storage_path / f".{document_id}.lock"
            lock_file = await asyncio.to_thread(self._acquire_file_lock, lock_path)
            try:
                yield
            finally:
                await asyncio.to_thread(self._release_file_lock, lock_file)

    def _acquire_file_lock(self, lock_path: Path) -> BinaryIO:
        """Acquire an operating-system-managed cross-process document lock."""

        deadline = time.monotonic() + self._LOCK_TIMEOUT_SECONDS

        while True:
            lock_file = lock_path.open("a+b")
            try:
                self._try_lock_file(lock_file)
                return lock_file
            except OSError as exc:
                lock_file.close()
                if not self._is_lock_contention(exc):
                    raise ChunkStorageWriteError(
                        f"Could not acquire chunk storage lock '{lock_path.name}'."
                    ) from exc
                if time.monotonic() >= deadline:
                    raise ChunkStorageWriteError(
                        f"Timed out waiting for chunk storage lock '{lock_path.name}'."
                    )
                time.sleep(self._LOCK_RETRY_SECONDS)

    def _release_file_lock(self, lock_file: BinaryIO) -> None:
        """Release an operating-system-managed document lock and close its file."""

        try:
            if os.name == "nt":
                import msvcrt

                lock_file.seek(0)
                msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
        finally:
            lock_file.close()

    def _try_lock_file(self, lock_file: BinaryIO) -> None:
        """Attempt a non-blocking operating-system lock on an open lock file."""

        if os.name == "nt":
            import msvcrt

            lock_file.seek(0, os.SEEK_END)
            if lock_file.tell() == 0:
                lock_file.write(b"\0")
                lock_file.flush()
                os.fsync(lock_file.fileno())
            lock_file.seek(0)
            msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
            return

        import fcntl

        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

    def _is_lock_contention(self, error: OSError) -> bool:
        """Return whether an OS lock error means another writer owns it."""

        return error.errno in {errno.EACCES, errno.EAGAIN} or getattr(
            error, "winerror", None
        ) in {32, 33}

    def _prepare_chunks_for_append(self, document_path: Path) -> int:
        """Make an existing generation range-safe and return the append offset."""

        chunks_path = document_path / "chunks.jsonl"
        manifest_path = document_path / "manifest.json"
        chunk_offset = chunks_path.stat().st_size if chunks_path.exists() else 0

        if not manifest_path.exists():
            return chunk_offset

        manifest = self._read_json(manifest_path)
        has_chunk_offset = "chunk_offset" in manifest
        has_chunk_length = "chunk_length" in manifest

        if has_chunk_offset != has_chunk_length:
            raise ChunkStorageCorruptionError(
                f"Chunk generation range is invalid for '{document_path.name}'."
            )

        if not has_chunk_offset:
            manifest["chunk_offset"] = 0
            manifest["chunk_length"] = chunk_offset
            manifest_bytes = json.dumps(
                manifest,
                ensure_ascii=False,
                separators=(",", ":"),
            ).encode("utf-8")
            self._replace_manifest(document_path, manifest_bytes)

        return chunk_offset

    def _read_chunk_generation(self, chunks_path: Path, manifest: dict) -> bytes:
        """Read exactly the JSONL generation referenced by a manifest."""

        if not chunks_path.exists():
            raise ChunkStorageCorruptionError(
                "Chunk manifest exists but JSONL is missing for "
                f"'{chunks_path.parent.name}'."
            )

        chunk_offset = manifest.get("chunk_offset")
        chunk_length = manifest.get("chunk_length")
        if chunk_offset is None and chunk_length is None:
            chunk_offset = 0
            chunk_length = chunks_path.stat().st_size

        if (
            not isinstance(chunk_offset, int)
            or isinstance(chunk_offset, bool)
            or chunk_offset < 0
            or not isinstance(chunk_length, int)
            or isinstance(chunk_length, bool)
            or chunk_length <= 0
        ):
            raise ChunkStorageCorruptionError(
                f"Chunk generation range is invalid for '{chunks_path.parent.name}'."
            )

        with chunks_path.open("rb") as file:
            file.seek(chunk_offset)
            generation = file.read(chunk_length)

        if len(generation) != chunk_length:
            raise ChunkStorageCorruptionError(
                f"Chunk generation is incomplete for '{chunks_path.parent.name}'."
            )
        return generation

    def _read_json(self, path: Path) -> dict:
        """Read one JSON object from storage."""

        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ChunkStorageCorruptionError(
                f"Could not read chunk manifest '{path}'."
            ) from exc

        if not isinstance(value, dict):
            raise ChunkStorageCorruptionError(
                f"Chunk manifest '{path}' is not an object."
            )
        return value

    def _read_manifest_generation(self, manifest: dict, document_id: str) -> str:
        """Validate the manifest identity and return its active generation."""

        if manifest.get("schema_version") != self._SCHEMA_VERSION:
            raise ChunkStorageCorruptionError(
                f"Unsupported manifest version for '{document_id}'."
            )
        if manifest.get("document_id") != document_id:
            raise ChunkStorageCorruptionError(
                f"Manifest document ID mismatch for '{document_id}'."
            )

        generation = manifest.get("generation")
        if not isinstance(generation, str) or not generation:
            raise ChunkStorageCorruptionError(
                f"Manifest generation is invalid for '{document_id}'."
            )
        return generation

    def _document_path(self, document_id: str) -> Path:
        """Return the validated local directory for one document."""

        self._validate_identifier(document_id, field_name="document_id")
        return self.storage_path / document_id

    def _chunks_path(self, document_id: str) -> Path:
        """Return the JSONL path for one document."""

        return self._document_path(document_id) / "chunks.jsonl"

    def _manifest_path(self, document_id: str) -> Path:
        """Return the manifest path for one document."""

        return self._document_path(document_id) / "manifest.json"

    def _validate_identifier(self, value: str, *, field_name: str) -> None:
        """Reject identifiers that are unsafe for document-local filesystem paths."""

        if not value or value in {".", ".."}:
            raise ChunkStorageValidationError(f"{field_name} must not be empty.")
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", value):
            raise ChunkStorageValidationError(
                f"{field_name} must be a single safe path component."
            )

    def _build_chunk_id(self, chunk: StoredChunk, text_sha256: str) -> str:
        """Create a deterministic ID for a chunk that has no supplied identifier."""

        value = ":".join(
            (
                chunk.document_id,
                str(chunk.page_number),
                str(chunk.chunk_index),
                text_sha256,
            )
        )
        return str(uuid5(NAMESPACE_URL, value))

    async def delete_document(self, *, document_id: str) -> bool:
        """Remove all chunks for a document. Return True when data was removed."""

        document_path = self.storage_path / document_id
        if not await asyncio.to_thread(document_path.exists):
            return False

        async with self._locked_document(document_id):
            await asyncio.to_thread(
                shutil.rmtree, str(document_path), ignore_errors=True
            )
            self._cache.pop(document_id, None)

        return True

    def _sha256(self, contents: bytes) -> str:
        """Return the hexadecimal SHA-256 checksum for persisted content."""

        return hashlib.sha256(contents).hexdigest()

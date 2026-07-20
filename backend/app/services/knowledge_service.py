import asyncio
import json
import os
import shutil
from pathlib import Path
from uuid import uuid4

from bson import ObjectId
from fastapi import UploadFile
from filelock import FileLock

from app.core.config import settings
from app.database.collections import get_knowledge_collection
from app.models.knowledge import create_document
from app.schemas.knowledge import KnowledgeDocument, KnowledgeDocumentResponse
from app.services.chunking_service import chunking_service
from app.services.embedding_service import embedding_service
from app.services.pdf_service import pdf_service
from app.services.storage import ChunkStorage, LocalChunkStorage, StoredChunk
from app.services.storage_service import storage_service
from app.services.vector_service import VectorReference, VectorService, vector_service

# Maximum characters per document before chunking (larger for dataset text).
_TEXT_CHUNK_SIZE = 1000
_TEXT_CHUNK_OVERLAP = 150


class KnowledgeService:
    """
    Handles knowledge document ingestion and retrieval.
    """

    def __init__(self, chunk_storage: ChunkStorage | None = None) -> None:
        """Initialize ingestion with the configured canonical chunk storage."""

        self.chunk_storage = (
            chunk_storage if chunk_storage is not None else LocalChunkStorage()
        )

    async def migrate_legacy_vector_mapping(self) -> bool:
        """Rebuild a legacy FAISS mapping from canonical local chunk storage."""

        vector_path = Path(settings.FAISS_INDEX_PATH)
        mapping_path = vector_path / settings.FAISS_MAPPING_NAME
        if not await asyncio.to_thread(mapping_path.exists):
            return False

        # Fast-path: if the mapping is already structured, no migration needed.
        mapping = await asyncio.to_thread(self._read_vector_mapping, mapping_path)
        if self._is_structured_vector_mapping(mapping):
            return False

        await asyncio.to_thread(vector_path.mkdir, parents=True, exist_ok=True)
        migration_lock = FileLock(str(vector_path / ".mapping-migration.lock"))
        await asyncio.to_thread(migration_lock.acquire, timeout=30)

        try:
            # Re-read under the lock in case another process migrated.
            mapping = await asyncio.to_thread(self._read_vector_mapping, mapping_path)
            if self._is_structured_vector_mapping(mapping):
                return False
            if not self._is_legacy_vector_mapping(mapping):
                raise RuntimeError(
                    "FAISS mapping format is invalid and cannot be migrated safely."
                )
            if not isinstance(self.chunk_storage, LocalChunkStorage):
                raise RuntimeError(
                    "Legacy FAISS migration requires LocalChunkStorage enumeration."
                )

            stored_chunks = await self._load_all_canonical_chunks()
            vector_references: list[VectorReference] = [
                {
                    "document_id": chunk.document_id,
                    "chunk_id": self._require_chunk_id(chunk),
                }
                for chunk in stored_chunks
            ]

            migration_path = vector_path / f".migration-{uuid4().hex}"
            await asyncio.to_thread(migration_path.mkdir, parents=True)

            try:
                migration_service = await asyncio.to_thread(
                    VectorService,
                    migration_path,
                )
                if stored_chunks:
                    embeddings = await asyncio.to_thread(
                        embedding_service.embed_batch,
                        [chunk.text for chunk in stored_chunks],
                    )
                    await asyncio.to_thread(
                        migration_service.rebuild,
                        vector_references,
                        embeddings,
                    )
                else:
                    await asyncio.to_thread(migration_service.save)

                await asyncio.to_thread(VectorService, migration_path)
                await asyncio.to_thread(
                    self._promote_vector_migration,
                    migration_path,
                    vector_path,
                )
            finally:
                await asyncio.to_thread(
                    shutil.rmtree,
                    migration_path,
                    ignore_errors=True,
                )

            return True
        finally:
            await asyncio.to_thread(migration_lock.release)

    async def _load_all_canonical_chunks(self) -> list[StoredChunk]:
        """Load every canonical document generation in stable document order."""

        if not isinstance(self.chunk_storage, LocalChunkStorage):
            return []

        storage_path = self.chunk_storage.storage_path
        if not await asyncio.to_thread(storage_path.exists):
            return []

        document_ids = await asyncio.to_thread(
            lambda: sorted(
                path.name for path in storage_path.iterdir() if path.is_dir()
            )
        )

        chunks: list[StoredChunk] = []
        for document_id in document_ids:
            chunks.extend(await self.chunk_storage.load_chunks(document_id=document_id))
        return chunks

    @staticmethod
    def _read_vector_mapping(mapping_path: Path) -> object:
        """Read a persisted vector mapping for migration classification."""

        try:
            return json.loads(mapping_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(
                "Could not read the FAISS mapping for migration."
            ) from exc

    @staticmethod
    def _is_structured_vector_mapping(mapping: object) -> bool:
        """Return whether every mapping entry contains both required identifiers."""

        return isinstance(mapping, list) and all(
            isinstance(reference, dict)
            and isinstance(reference.get("document_id"), str)
            and bool(reference["document_id"])
            and isinstance(reference.get("chunk_id"), str)
            and bool(reference["chunk_id"])
            for reference in mapping
        )

    @staticmethod
    def _is_legacy_vector_mapping(mapping: object) -> bool:
        """Return whether a mapping consists only of legacy chunk identifiers."""

        return (
            isinstance(mapping, list)
            and bool(mapping)
            and all(isinstance(chunk_id, str) and chunk_id for chunk_id in mapping)
        )

    @staticmethod
    def _promote_vector_migration(
        migration_path: Path,
        vector_path: Path,
    ) -> None:
        """Back up legacy vector files and promote a validated replacement."""

        file_names = (settings.FAISS_INDEX_NAME, settings.FAISS_MAPPING_NAME)
        backup_token = uuid4().hex
        backups: dict[Path, Path] = {}

        for file_name in file_names:
            active_path = vector_path / file_name
            if active_path.exists():
                backup_path = vector_path / f"{file_name}.legacy-{backup_token}.bak"
                shutil.copy2(active_path, backup_path)
                backups[active_path] = backup_path

        try:
            for file_name in file_names:
                os.replace(migration_path / file_name, vector_path / file_name)
        except OSError:
            for active_path, backup_path in backups.items():
                shutil.copy2(backup_path, active_path)
            raise

    async def save_upload(
        self,
        *,
        user_id: str,
        upload_file: UploadFile,
    ) -> KnowledgeDocumentResponse:
        """
        Upload a PDF, extract its contents, create chunks,
        and persist both metadata and chunks.

        On any failure after upload begins, all state is rolled back
        so the system remains consistent.
        """

        # ---------------------------------------------------------
        # Phase 1 — save file to disk
        # ---------------------------------------------------------
        stored_path: Path = await storage_service.save_pdf(upload_file)
        document_id: str | None = None

        try:
            # ---------------------------------------------------------
            # Validate PDF
            # ---------------------------------------------------------
            pdf_service.validate_pdf(
                stored_path,
                max_size_mb=settings.MAX_UPLOAD_SIZE_MB,
            )

            # ---------------------------------------------------------
            # Extract text
            # ---------------------------------------------------------
            pages = pdf_service.extract_pages(stored_path)

            page_count = len(pages)

            # ---------------------------------------------------------
            # Create metadata document
            # ---------------------------------------------------------
            document = create_document(
                user_id=user_id,
                filename=stored_path.name,
                original_filename=upload_file.filename or stored_path.name,
                content_type=upload_file.content_type or "application/pdf",
                storage_path=str(stored_path),
                file_size=stored_path.stat().st_size,
                page_count=page_count,
            )

            documents = get_knowledge_collection()

            result = await documents.insert_one(document.model_dump(exclude={"id"}))

            document.id = str(result.inserted_id)
            document_id = document.id

            # ---------------------------------------------------------
            # Create chunks
            # ---------------------------------------------------------
            chunks = chunking_service.chunk_document(
                document_id=document.id,
                user_id=user_id,
                pages=pages,
            )

            # ---------------------------------------------------------
            # Save chunks to JSONL and FAISS
            # ---------------------------------------------------------
            if chunks:
                embeddings = embedding_service.embed_batch(
                    [chunk.text for chunk in chunks]
                )

                stored_chunks = await self.chunk_storage.save_chunks(
                    chunks=[
                        StoredChunk(
                            document_id=chunk.document_id,
                            page_number=chunk.page_number,
                            chunk_index=chunk.chunk_index,
                            text=chunk.text,
                            created_at=chunk.created_at,
                        )
                        for chunk in chunks
                    ]
                )

                vector_references: list[VectorReference] = [
                    {
                        "document_id": stored_chunk.document_id,
                        "chunk_id": self._require_chunk_id(stored_chunk),
                    }
                    for stored_chunk in stored_chunks
                ]

                vector_service.instance.add(
                    vector_references,
                    embeddings,
                )

                vector_service.instance.save()

            # ---------------------------------------------------------
            # Update metadata to "processed"
            # ---------------------------------------------------------
            await documents.update_one(
                {"_id": ObjectId(document.id)},
                {
                    "$set": {
                        "chunk_count": len(chunks),
                        "status": "processed",
                    }
                },
            )

            document.chunk_count = len(chunks)
            document.status = "processed"

            return self._to_response(document)

        except BaseException:
            await self._rollback_upload(
                document_id=document_id,
                stored_path=stored_path,
            )
            raise

    async def ingest_text(
        self,
        *,
        user_id: str,
        title: str,
        category: str,
        source: str,
        text: str,
        page_number: int = 1,
    ) -> KnowledgeDocumentResponse:
        """
        Ingest raw text directly into the knowledge system, bypassing the PDF
        upload pipeline.  Uses the same chunking, embedding, storage, and
        indexing path as save_upload.

        On any failure the partial state for the current document is rolled
        back so the system remains consistent.
        """

        pages = [text]
        document_id: str | None = None

        # Build a synthetic filename from the title for display.
        safe_title = "".join(c if c.isalnum() or c in " _-" else "_" for c in title)
        filename = f"{safe_title[:64]}.txt"

        try:
            # ---------------------------------------------------------
            # Create metadata document
            # ---------------------------------------------------------
            document = create_document(
                user_id=user_id,
                filename=filename,
                original_filename=f"{source} / {category} / {title}",
                content_type="text/plain",
                storage_path="",
                file_size=len(text.encode("utf-8")),
                page_count=page_number,
                source=source,
            )

            documents = get_knowledge_collection()
            result = await documents.insert_one(document.model_dump(exclude={"id"}))
            document.id = str(result.inserted_id)
            document_id = document.id
            document_id = document.id

            # ---------------------------------------------------------
            # Create chunks
            # ---------------------------------------------------------
            chunks = chunking_service.chunk_document(
                document_id=document.id,
                user_id=user_id,
                pages=pages,
            )

            # ---------------------------------------------------------
            # Save chunks to JSONL and FAISS
            # ---------------------------------------------------------
            if chunks:
                embeddings = embedding_service.embed_batch(
                    [chunk.text for chunk in chunks]
                )

                stored_chunks = await self.chunk_storage.save_chunks(
                    chunks=[
                        StoredChunk(
                            document_id=chunk.document_id,
                            page_number=chunk.page_number,
                            chunk_index=chunk.chunk_index,
                            text=chunk.text,
                            created_at=chunk.created_at,
                        )
                        for chunk in chunks
                    ]
                )

                vector_references: list[VectorReference] = [
                    {
                        "document_id": stored_chunk.document_id,
                        "chunk_id": self._require_chunk_id(stored_chunk),
                    }
                    for stored_chunk in stored_chunks
                ]

                vector_service.instance.add(
                    vector_references,
                    embeddings,
                )

                vector_service.instance.save()

            # ---------------------------------------------------------
            # Update metadata to "processed"
            # ---------------------------------------------------------
            await documents.update_one(
                {"_id": ObjectId(document.id)},
                {
                    "$set": {
                        "chunk_count": len(chunks),
                        "status": "processed",
                    }
                },
            )

            document.chunk_count = len(chunks)
            document.status = "processed"

            return self._to_response(document)

        except BaseException:
            await self._rollback_upload(
                document_id=document_id,
                stored_path=None,
            )
            raise

    async def _rollback_upload(
        self,
        *,
        document_id: str | None,
        stored_path: Path | None,
    ) -> None:
        """Remove all state created by a failed upload. Safe to call multiple times."""

        errors: list[str] = []

        # Remove MongoDB document metadata
        if document_id is not None:
            try:
                documents = get_knowledge_collection()
                await documents.delete_one({"_id": ObjectId(document_id)})
            except Exception as exc:
                errors.append(f"MongoDB cleanup: {exc}")

        # Remove ChunkStorage document
        if document_id is not None:
            try:
                await self.chunk_storage.delete_document(document_id=document_id)
            except Exception as exc:
                errors.append(f"ChunkStorage cleanup: {exc}")

        # Remove FAISS vectors
        if document_id is not None:
            try:
                vector_service.instance.remove_document(document_id)
            except Exception as exc:
                errors.append(f"FAISS cleanup: {exc}")

        # Remove uploaded PDF
        if stored_path is not None:
            try:
                await asyncio.to_thread(stored_path.unlink, missing_ok=True)
            except Exception as exc:
                errors.append(f"PDF cleanup: {exc}")

        if errors:
            raise RuntimeError(
                "Partial rollback after ingestion failure: " + "; ".join(errors)
            )

    async def delete_document(
        self,
        *,
        document_id: str,
    ) -> bool:
        """
        Completely remove a document and all its associated state.
        Returns True when a document was removed, False if none existed.

        Idempotent — deleting a non-existing document does not corrupt state.
        """

        if not ObjectId.is_valid(document_id):
            return False

        documents = get_knowledge_collection()
        doc = await documents.find_one({"_id": ObjectId(document_id)})
        if doc is None:
            return False

        # Collect state before deletion
        stored_path: Path | None = None
        raw_path = doc.get("storage_path", "")
        if raw_path:
            candidate = Path(raw_path)
            if candidate.exists():
                stored_path = candidate

        # Remove MongoDB metadata
        await documents.delete_one({"_id": ObjectId(document_id)})

        # Remove ChunkStorage document
        await self.chunk_storage.delete_document(document_id=document_id)

        # Remove FAISS vectors
        vector_service.instance.remove_document(document_id)

        # Remove uploaded PDF
        if stored_path is not None:
            await asyncio.to_thread(stored_path.unlink, missing_ok=True)

        return True

    @staticmethod
    def _require_chunk_id(chunk: StoredChunk) -> str:
        """Return the stable identifier guaranteed by persisted chunk storage."""

        if chunk.id is None:
            raise RuntimeError(
                "ChunkStorage returned a chunk without a stable identifier."
            )
        return chunk.id

    async def list_documents(
        self,
        *,
        user_id: str,
    ) -> list[KnowledgeDocumentResponse]:
        """
        Return all uploaded knowledge documents
        belonging to the authenticated user.
        """

        collection = get_knowledge_collection()

        cursor = collection.find(
            {
                "user_id": user_id,
            }
        ).sort("uploaded_at", -1)

        documents = await cursor.to_list(length=None)

        return [
            self._to_response(
                KnowledgeDocument(
                    id=str(document["_id"]),
                    user_id=document["user_id"],
                    filename=document["filename"],
                    original_filename=document["original_filename"],
                    content_type=document["content_type"],
                    storage_path=document["storage_path"],
                    file_size=document["file_size"],
                    page_count=document["page_count"],
                    chunk_count=document.get("chunk_count", 0),
                    status=document.get("status", "uploaded"),
                    source=document.get("source", "upload"),
                    uploaded_at=document["uploaded_at"],
                )
            )
            for document in documents
        ]

    @staticmethod
    def _to_response(doc: KnowledgeDocument) -> KnowledgeDocumentResponse:
        """Convert an internal KnowledgeDocument to its public DTO."""
        return KnowledgeDocumentResponse(
            id=doc.id or "",
            user_id=doc.user_id,
            filename=doc.filename,
            original_filename=doc.original_filename,
            content_type=doc.content_type,
            file_size=doc.file_size,
            page_count=doc.page_count,
            chunk_count=doc.chunk_count,
            status=doc.status,
            source=doc.source,
            uploaded_at=doc.uploaded_at,
        )


knowledge_service = KnowledgeService()

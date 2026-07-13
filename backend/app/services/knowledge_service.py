from pathlib import Path

from bson import ObjectId
from fastapi import UploadFile

from app.core.config import settings
from app.database.collections import (
    get_knowledge_chunks_collection,
    get_knowledge_collection,
)
from app.models.knowledge import create_document
from app.schemas.knowledge import KnowledgeDocument
from app.services.chunking_service import chunking_service
from app.services.pdf_service import pdf_service
from app.services.storage_service import storage_service


class KnowledgeService:
    """
    Handles knowledge document ingestion and retrieval.
    """

    async def save_upload(
        self,
        *,
        user_id: str,
        upload_file: UploadFile,
    ) -> KnowledgeDocument:
        """
        Upload a PDF, extract its contents, create chunks,
        and persist both metadata and chunks.
        """

        # ---------------------------------------------------------
        # Save uploaded file
        # ---------------------------------------------------------
        stored_path: Path = await storage_service.save_pdf(upload_file)

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

        # ---------------------------------------------------------
        # Create chunks
        # ---------------------------------------------------------
        chunks = chunking_service.chunk_document(
            document_id=document.id,
            user_id=user_id,
            pages=pages,
        )

        # ---------------------------------------------------------
        # Save chunks
        # ---------------------------------------------------------
        if chunks:

            chunk_collection = get_knowledge_chunks_collection()

            await chunk_collection.insert_many(
                [chunk.model_dump(exclude={"id"}) for chunk in chunks]
            )

        # ---------------------------------------------------------
        # Update metadata
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

        return document

    async def list_documents(
        self,
        *,
        user_id: str,
    ) -> list[KnowledgeDocument]:
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
                uploaded_at=document["uploaded_at"],
            )
            for document in documents
        ]


knowledge_service = KnowledgeService()

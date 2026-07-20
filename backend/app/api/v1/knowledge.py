from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.api.deps import get_current_user
from app.models.user import UserDocument
from app.schemas.dataset import (
    DatasetIngestionRequest,
    DatasetIngestionResponse,
    DatasetResponse,
)
from app.schemas.knowledge import KnowledgeDocumentResponse
from app.schemas.retrieval import RetrievalResult
from app.services.dataset_service import dataset_service
from app.services.knowledge_service import knowledge_service
from app.services.retrieval_service import retrieval_service

router = APIRouter(
    prefix="/knowledge",
    tags=["Knowledge Base"],
)


async def get_current_admin(
    current_user: UserDocument = Depends(get_current_user),
) -> UserDocument:
    """Require the authenticated user to hold the administrator role."""

    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access is required.",
        )
    return current_user


@router.post(
    "/upload",
    response_model=KnowledgeDocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    file: UploadFile = File(...),
    current_user: UserDocument = Depends(get_current_admin),
):
    """
    Upload a PDF into the global knowledge base.
    """

    try:
        return await knowledge_service.save_upload(
            user_id=current_user.id,
            upload_file=file,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get("", response_model=list[KnowledgeDocumentResponse])
async def list_documents(
    current_user: UserDocument = Depends(get_current_user),
):
    """
    Return all documents uploaded by the authenticated user.
    """

    return await knowledge_service.list_documents(
        user_id=current_user.id,
    )


@router.get("/search", response_model=list[RetrievalResult])
async def search_documents(
    query: str,
    current_user: UserDocument = Depends(get_current_user),
):
    return await retrieval_service.retrieve(
        query=query,
    )


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_document(
    document_id: str,
    current_user: UserDocument = Depends(get_current_admin),
):
    """
    Permanently delete a knowledge document and all its associated data.
    """

    removed = await knowledge_service.delete_document(document_id=document_id)
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )


# ---------------------------------------------------------------------------
# Dataset endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/datasets",
    response_model=list[DatasetResponse],
)
async def list_datasets(
    current_user: UserDocument = Depends(get_current_admin),
):
    """
    Return all available datasets with their ingestion status.
    """

    datasets = await dataset_service.get_available_datasets(
        user_id=current_user.id,
    )

    return [
        DatasetResponse(
            name=ds.name,
            display_name=ds.display_name,
            description=ds.description,
            source=ds.source,
            is_ingested=ds.is_ingested,
            document_count=ds.document_count,
            chunk_count=ds.chunk_count,
            ingested_at=ds.ingested_at,
        )
        for ds in datasets
    ]


@router.post(
    "/ingest-datasets",
    response_model=DatasetIngestionResponse,
)
async def ingest_datasets(
    body: DatasetIngestionRequest | None = None,
    current_user: UserDocument = Depends(get_current_admin),
):
    """
    Trigger ingestion of datasets. Ingests all uningested datasets by default,
    or a specific dataset if ``dataset`` is provided.
    """

    force = body.force if body else False
    dataset_name = body.dataset if body else None

    if dataset_name:
        success, message = await dataset_service.ingest_dataset(
            dataset_name,
            user_id=current_user.id,
            force=force,
        )

        if not success and "Unknown dataset" in message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=message,
            )

        return DatasetIngestionResponse(
            ingested=(
                [dataset_name] if success and "already ingested" not in message else []
            ),
            skipped=[dataset_name] if success and "already ingested" in message else [],
            failed=[] if success else [[dataset_name, message]],
            message=message,
        )

    result = await dataset_service.ingest_all_datasets(
        user_id=current_user.id,
        force=force,
    )

    parts: list[str] = []
    if result.ingested:
        parts.append(f"Ingested: {', '.join(result.ingested)}")
    if result.skipped:
        parts.append(f"Skipped: {', '.join(result.skipped)}")
    if result.failed:
        failed_names = [name for name, _ in result.failed]
        parts.append(f"Failed: {', '.join(failed_names)}")

    return DatasetIngestionResponse(
        ingested=result.ingested,
        skipped=result.skipped,
        failed=[[name, msg] for name, msg in result.failed],
        message="; ".join(parts) if parts else "No datasets to process.",
    )

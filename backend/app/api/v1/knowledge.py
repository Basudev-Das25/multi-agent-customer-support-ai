from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.api.deps import get_current_user
from app.models.user import UserDocument
from app.services.knowledge_service import knowledge_service
from app.services.retrieval_service import retrieval_service

router = APIRouter(
    prefix="/knowledge",
    tags=["Knowledge Base"],
)


@router.post(
    "/upload",
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    file: UploadFile = File(...),
    current_user: UserDocument = Depends(get_current_user),
):
    """
    Upload a PDF into the user's knowledge base.
    """

    try:
        document = await knowledge_service.save_upload(
            user_id=current_user.id,
            upload_file=file,
        )

        return document

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get("")
async def list_documents(
    current_user: UserDocument = Depends(get_current_user),
):
    """
    Return all documents uploaded by the authenticated user.
    """

    return await knowledge_service.list_documents(
        user_id=current_user.id,
    )


@router.get("/search")
async def search_documents(
    query: str,
    current_user: UserDocument = Depends(get_current_user),
):
    return await retrieval_service.retrieve(
        query=query,
        user_id=current_user.id,
    )

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.models.user import UserDocument
from app.schemas.chat import (
    ConversationResponse,
    ConversationSummary,
    SendMessageRequest,
)
from app.services.chat_service import get_conversation, list_conversations, send_message

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.get("/conversations", response_model=list[ConversationSummary])
async def read_conversations(
    current_user: Annotated[UserDocument, Depends(get_current_user)],
) -> list[ConversationSummary]:
    return await list_conversations(current_user.id or "")


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def read_conversation(
    conversation_id: str,
    current_user: Annotated[UserDocument, Depends(get_current_user)],
) -> ConversationResponse:
    conversation = await get_conversation(current_user.id or "", conversation_id)
    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        )
    return conversation


@router.post(
    "/messages",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_message(
    request: SendMessageRequest,
    current_user: Annotated[UserDocument, Depends(get_current_user)],
) -> ConversationResponse:
    return await send_message(
        current_user.id or "", request.content, request.conversation_id
    )

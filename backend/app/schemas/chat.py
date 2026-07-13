from datetime import datetime
from typing import Literal

from pydantic import Field

from app.schemas.base import BaseSchema

MessageRole = Literal["user", "assistant"]


class ChatMessage(BaseSchema):
    id: str
    role: MessageRole
    content: str
    created_at: datetime


class SendMessageRequest(BaseSchema):
    content: str = Field(min_length=1, max_length=4_000)
    conversation_id: str | None = None


class ConversationResponse(BaseSchema):
    id: str
    title: str
    messages: list[ChatMessage]
    created_at: datetime
    updated_at: datetime


class ConversationSummary(BaseSchema):
    id: str
    title: str
    updated_at: datetime

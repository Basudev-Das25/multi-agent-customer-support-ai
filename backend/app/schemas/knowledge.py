from datetime import datetime

from app.schemas.base import BaseSchema


class KnowledgeDocument(BaseSchema):
    id: str | None = None

    user_id: str

    filename: str

    original_filename: str

    content_type: str

    storage_path: str

    file_size: int

    page_count: int

    chunk_count: int = 0

    status: str = "uploaded"

    source: str = "upload"

    uploaded_at: datetime


class KnowledgeDocumentResponse(BaseSchema):
    """Public DTO returned to API consumers — excludes internal paths."""

    id: str

    user_id: str

    filename: str

    original_filename: str

    content_type: str

    file_size: int

    page_count: int

    chunk_count: int

    status: str

    source: str

    uploaded_at: datetime


class KnowledgeChunk(BaseSchema):
    id: str | None = None

    document_id: str

    user_id: str

    page_number: int

    chunk_index: int

    text: str

    created_at: datetime

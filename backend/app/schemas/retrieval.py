from app.schemas.base import BaseSchema


class VectorSearchResult(BaseSchema):
    chunk_id: str
    score: float


class RetrievalResult(BaseSchema):
    chunk_id: str
    document_id: str
    page_number: int
    chunk_index: int
    text: str
    score: float

from app.schemas.base import BaseSchema


class DatasetResponse(BaseSchema):
    """Public DTO for one dataset's ingestion status."""

    name: str
    display_name: str
    description: str
    source: str
    is_ingested: bool
    document_count: int
    chunk_count: int
    ingested_at: str | None


class DatasetIngestionRequest(BaseSchema):
    """Request body for triggering dataset ingestion."""

    dataset: str | None = None
    """If set, ingest only this dataset. If None, ingest all uningested datasets."""

    force: bool = False
    """If True, re-ingest even if already ingested."""


class DatasetIngestionResponse(BaseSchema):
    """Response after triggering dataset ingestion."""

    ingested: list[str]
    skipped: list[str]
    failed: list[list[str]]
    message: str

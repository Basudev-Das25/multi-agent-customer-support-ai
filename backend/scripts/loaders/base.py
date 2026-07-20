"""Common types and the loader protocol for dataset ingestion."""

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class DocumentInput:
    """One document to be ingested into the knowledge base."""

    title: str
    """Human-readable title — appears in the document list."""

    category: str
    """Dataset-specific category or intent label."""

    source: str
    """Source dataset name, e.g. ``"banking77"``."""

    text: str
    """The full text content that will be chunked and indexed."""

    metadata: dict[str, str] = field(default_factory=dict)
    """Optional key/value pairs attached to the document for provenance."""


@runtime_checkable
class DatasetLoader(Protocol):
    """Ingest a dataset and yield one DocumentInput per logical document."""

    def load(self) -> Iterable[DocumentInput]:
        """Yield documents from the dataset.

        May raise :class:`FileNotFoundError` when *path* does not exist,
        or :class:`ValueError` when the data format is unrecognised.
        """
        ...

import json
from pathlib import Path

import faiss
import numpy as np

from app.core.config import settings
from app.schemas.retrieval import VectorSearchResult
from app.services.embedding_service import embedding_service


class VectorService:
    """
    Handles FAISS vector indexing and similarity search.
    """

    def __init__(
        self,
        storage_path: Path | None = None,
    ) -> None:

        self.storage_path = (
            storage_path
            if storage_path is not None
            else Path(settings.FAISS_INDEX_PATH)
        )
        self.storage_path.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.index_file = self.storage_path / settings.FAISS_INDEX_NAME

        self.mapping_file = self.storage_path / settings.FAISS_MAPPING_NAME

        self.dimension = embedding_service.dimension()

        self.index = faiss.IndexFlatIP(self.dimension)

        self.mapping: list[str] = []

        self.load()

    def add(
        self,
        chunk_ids: list[str],
        embeddings: np.ndarray,
    ) -> None:

        if len(chunk_ids) == 0:
            return
        if embeddings.size == 0:
            return

        self.index.add(embeddings)

        self.mapping.extend(chunk_ids)

    def search(
        self,
        query_embedding: np.ndarray,
        k: int | None = None,
    ) -> list[VectorSearchResult]:

        if self.index.ntotal == 0:
            return []

        if query_embedding.ndim == 1:
            query_embedding = np.expand_dims(
                query_embedding,
                axis=0,
            )

        k = min(
            k or settings.TOP_K_RESULTS,
            self.index.ntotal,
        )

        scores, indices = self.index.search(
            query_embedding,
            k,
        )

        results = []

        for score, idx in zip(
            scores[0],
            indices[0],
        ):

            if idx == -1:
                continue

            results.append(
                VectorSearchResult(
                    chunk_id=self.mapping[idx],
                    score=float(score),
                )
            )

        return results

    def save(self) -> None:

        faiss.write_index(
            self.index,
            str(self.index_file),
        )

        with open(
            self.mapping_file,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                self.mapping,
                file,
                indent=2,
            )

    def load(self) -> None:
        try:
            if self.index_file.exists():

                self.index = faiss.read_index(str(self.index_file))

            if self.mapping_file.exists():

                with open(
                    self.mapping_file,
                    encoding="utf-8",
                ) as file:

                    self.mapping = json.load(file)
                    if len(self.mapping) != self.index.ntotal:
                        raise RuntimeError(
                            "FAISS index and mapping.json are out of sync."
                        )
        except Exception:
            self.index = faiss.IndexFlatIP(self.dimension)

            self.mapping = []

    def rebuild(
        self,
        chunk_ids: list[str],
        embeddings: np.ndarray,
    ) -> None:

        self.index = faiss.IndexFlatIP(self.dimension)

        self.mapping = []

        self.add(
            chunk_ids,
            embeddings,
        )

        self.save()


vector_service = VectorService()

from functools import lru_cache

import numpy as np
from sentence_transformers import SentenceTransformer

from app.core.config import settings


class EmbeddingService:
    """
    Handles embedding generation for RAG.
    """

    def __init__(self) -> None:
        self.model = SentenceTransformer(settings.EMBEDDING_MODEL)

    def embed(
        self,
        text: str,
    ) -> np.ndarray:
        """
        Generate embedding for a single text.
        """

        embedding = self.model.encode(
            text,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )

        return embedding.astype(np.float32)

    def embed_batch(
        self,
        texts: list[str],
    ) -> np.ndarray:
        """
        Generate embeddings for multiple texts.
        """

        embeddings = self.model.encode(
            texts,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )

        return embeddings.astype(np.float32)

    def dimension(self) -> int:
        """
        Return embedding dimension.
        """

        return self.model.get_embedding_dimension()


@lru_cache(maxsize=1)
def get_embedding_service() -> EmbeddingService:
    return EmbeddingService()


embedding_service = get_embedding_service()

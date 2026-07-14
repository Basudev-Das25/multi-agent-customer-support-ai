import uuid

import pytest

from app.services.embedding_service import embedding_service
from app.services.vector_service import VectorService


@pytest.mark.asyncio
async def test_retrieve(tmp_path):

    vector = VectorService(storage_path=tmp_path)

    texts = [
        "React Three Fiber is a React renderer.",
        "Password reset instructions.",
        "Refund policy information.",
    ]

    ids = [str(uuid.uuid4()) for _ in texts]

    embeddings = embedding_service.embed_batch(texts)

    vector.rebuild(
        ids,
        embeddings,
    )

    # This unit test will later be expanded to use the
    # fake Mongo collection provided by conftest.py.

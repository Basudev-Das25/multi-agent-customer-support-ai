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

    document_id = str(uuid.uuid4())
    ids = [str(uuid.uuid4()) for _ in texts]
    vector_references = [
        {"document_id": document_id, "chunk_id": chunk_id} for chunk_id in ids
    ]

    embeddings = embedding_service.embed_batch(texts)

    vector.rebuild(
        vector_references,
        embeddings,
    )

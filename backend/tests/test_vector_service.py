import uuid

from app.services.embedding_service import embedding_service
from app.services.vector_service import VectorService


def test_vector_search(tmp_path):

    vector_service = VectorService(storage_path=tmp_path)

    texts = [
        "Refund policy",
        "Internet troubleshooting",
        "Password reset",
    ]

    ids = [str(uuid.uuid4()) for _ in texts]

    embeddings = embedding_service.embed_batch(texts)

    vector_service.rebuild(
        ids,
        embeddings,
    )

    query = embedding_service.embed("How can I reset my password?")

    results = vector_service.search(
        query,
        k=2,
    )

    assert len(results) == 2

    assert results[0].chunk_id in ids

    assert isinstance(results[0].score, float)

    assert results[0].score > 0

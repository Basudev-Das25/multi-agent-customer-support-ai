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

    document_id = str(uuid.uuid4())
    ids = [str(uuid.uuid4()) for _ in texts]
    vector_references = [
        {"document_id": document_id, "chunk_id": chunk_id} for chunk_id in ids
    ]

    embeddings = embedding_service.embed_batch(texts)

    vector_service.rebuild(
        vector_references,
        embeddings,
    )

    query = embedding_service.embed("How can I reset my password?")

    results = vector_service.search(
        query,
        k=2,
    )

    assert len(results) == 2

    assert results[0].document_id == document_id
    assert results[0].chunk_id in ids

    assert isinstance(results[0].score, float)

    assert results[0].score > 0

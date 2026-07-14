from app.services.embedding_service import embedding_service


def test_single_embedding():

    embedding = embedding_service.embed("Hello world")

    assert embedding.ndim == 1

    assert len(embedding) == embedding_service.dimension()


def test_batch_embedding():

    embeddings = embedding_service.embed_batch(
        [
            "Hello",
            "World",
        ]
    )

    assert embeddings.shape[0] == 2

    assert embeddings.shape[1] == embedding_service.dimension()

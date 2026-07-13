from app.services.chunking_service import chunking_service


def test_chunk_document():

    pages = [
        "A" * 2500,
    ]

    chunks = chunking_service.chunk_document(
        document_id="doc1",
        user_id="user1",
        pages=pages,
    )

    assert len(chunks) >= 3

    assert chunks[0].page_number == 1

    assert chunks[0].chunk_index == 0

    assert chunks[-1].page_number == 1

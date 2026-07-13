from app.models.knowledge import create_chunk
from app.schemas.knowledge import KnowledgeChunk


class ChunkingService:
    """
    Splits extracted PDF text into overlapping chunks while
    preserving page information.
    """

    def __init__(
        self,
        chunk_size: int = 1000,
        overlap: int = 150,
    ):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_document(
        self,
        *,
        document_id: str,
        user_id: str,
        pages: list[str],
    ) -> list[KnowledgeChunk]:
        chunks: list[KnowledgeChunk] = []

        chunk_index = 0

        for page_number, page_text in enumerate(pages, start=1):

            text = page_text.strip()

            if not text:
                continue

            start = 0

            while start < len(text):

                end = min(
                    start + self.chunk_size,
                    len(text),
                )

                chunk = create_chunk(
                    document_id=document_id,
                    user_id=user_id,
                    page_number=page_number,
                    chunk_index=chunk_index,
                    text=text[start:end],
                )

                chunks.append(chunk)

                chunk_index += 1

                if end >= len(text):
                    break

                start = end - self.overlap

        return chunks


chunking_service = ChunkingService()

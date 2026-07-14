import re

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

    def _clean_text(
        self,
        text: str,
    ) -> str:
        """
        Normalize PDF extracted text.
        """

        # Remove citation markers like [1], [2], [15]
        text = re.sub(r"\[\d+\]", "", text)

        # Normalize spaces
        text = re.sub(r"[ \t]+", " ", text)

        # Normalize blank lines
        text = re.sub(r"\n{3,}", "\n\n", text)

        return text.strip()

    def _find_chunk_end(
        self,
        text: str,
        start: int,
    ) -> int:
        """
        Prefer ending chunks at sentence boundaries.
        """

        ideal_end = min(
            start + self.chunk_size,
            len(text),
        )

        if ideal_end == len(text):
            return ideal_end

        search_window = text[
            ideal_end : min(
                ideal_end + 200,
                len(text),
            )
        ]

        match = re.search(
            r"[.!?]\s",
            search_window,
        )

        if match:
            return ideal_end + match.end()

        return ideal_end

    def chunk_document(
        self,
        *,
        document_id: str,
        user_id: str,
        pages: list[str],
    ) -> list[KnowledgeChunk]:

        chunks: list[KnowledgeChunk] = []

        chunk_index = 0

        for page_number, page_text in enumerate(
            pages,
            start=1,
        ):

            text = self._clean_text(page_text)

            if not text:
                continue

            start = 0

            while start < len(text):

                end = self._find_chunk_end(
                    text,
                    start,
                )

                chunk = create_chunk(
                    document_id=document_id,
                    user_id=user_id,
                    page_number=page_number,
                    chunk_index=chunk_index,
                    text=text[start:end].strip(),
                )

                chunks.append(chunk)

                chunk_index += 1

                if end >= len(text):
                    break

                start = max(
                    end - self.overlap,
                    0,
                )

        return chunks


chunking_service = ChunkingService()

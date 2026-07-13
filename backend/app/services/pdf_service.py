from pathlib import Path

import filetype
import fitz


class PDFService:
    """
    Handles PDF validation and extraction.
    """

    def validate_pdf(
        self,
        path: Path,
        *,
        max_size_mb: int,
    ) -> None:

        if not path.exists():
            raise FileNotFoundError(path)

        size_mb = path.stat().st_size / (1024 * 1024)

        if size_mb > max_size_mb:
            raise ValueError(f"PDF exceeds {max_size_mb} MB.")

        kind = filetype.guess(path)

        if kind is None or kind.mime != "application/pdf":
            raise ValueError("Invalid PDF.")

    def extract_pages(
        self,
        path: Path,
    ) -> list[str]:

        document = fitz.open(path)

        pages: list[str] = []

        try:
            for page in document:

                pages.append(page.get_text("text"))

        finally:
            document.close()

        return pages

    def page_count(
        self,
        path: Path,
    ) -> int:

        document = fitz.open(path)

        try:
            return document.page_count

        finally:
            document.close()


pdf_service = PDFService()

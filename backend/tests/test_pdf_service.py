from pathlib import Path

import pytest

from app.services.pdf_service import pdf_service


def test_missing_pdf():

    with pytest.raises(FileNotFoundError):

        pdf_service.validate_pdf(
            Path("missing.pdf"),
            max_size_mb=20,
        )

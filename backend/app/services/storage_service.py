from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import settings


class StorageService:
    def __init__(self):
        self.storage_path = Path(settings.UPLOAD_DIRECTORY)

        self.storage_path.mkdir(
            parents=True,
            exist_ok=True,
        )

    async def save_pdf(
        self,
        file: UploadFile,
    ) -> Path:

        filename = f"{uuid4()}.pdf"

        destination = self.storage_path / filename

        contents = await file.read()

        destination.write_bytes(contents)

        await file.seek(0)

        return destination


storage_service = StorageService()

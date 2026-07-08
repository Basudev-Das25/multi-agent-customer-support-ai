from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase

from app.core.config import settings


class Database:
    def __init__(self):
        self.client: AsyncMongoClient | None = None
        self.db: AsyncDatabase | None = None

    async def connect(self) -> None:
        self.client = AsyncMongoClient(settings.MONGODB_URI)
        self.db = self.client[settings.DATABASE_NAME]

        await self.client.admin.command("ping")

    async def disconnect(self) -> None:
        if self.client is not None:
            self.client.close()

    @property
    def is_connected(self) -> bool:
        return self.db is not None

    def get_database(self):
        if self.db is None:
            raise RuntimeError("Database has not been initialized.")

        return self.db


database = Database()

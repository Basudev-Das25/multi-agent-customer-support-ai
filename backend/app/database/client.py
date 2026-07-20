from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase

from app.core.config import settings
from app.database.indexes import ensure_indexes


class Database:
    def __init__(self):
        self.client: AsyncMongoClient | None = None
        self.db: AsyncDatabase | None = None

    async def connect(self) -> None:
        self.client = AsyncMongoClient(settings.MONGODB_URI)
        self.db = self.client[settings.DATABASE_NAME]

        await self.client.admin.command("ping")
        await ensure_indexes(
            self.db[settings.USERS_COLLECTION],
            self.db[settings.CONVERSATIONS_COLLECTION],
            self.db[settings.KNOWLEDGE_COLLECTION],
            self.db["dataset_ingestion_log"],
        )

        from app.services.knowledge_service import knowledge_service

        await knowledge_service.migrate_legacy_vector_mapping()

    async def disconnect(self) -> None:
        if self.client is not None:
            await self.client.close()
            self.client = None
            self.db = None

    def get_database(self):
        if self.db is None:
            raise RuntimeError("Database has not been initialized.")

        return self.db


database = Database()

from pymongo import AsyncMongoClient

from app.core.config import settings


class Database:
    client: AsyncMongoClient | None = None
    db = None

    async def connect(self):
        self.client = AsyncMongoClient(settings.MONGODB_URI)
        self.db = self.client[settings.DATABASE_NAME]

        # Verify connection
        await self.client.admin.command("ping")

    async def disconnect(self):
        if self.client:
            self.client.close()


database = Database()

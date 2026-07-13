import pytest
from bson import ObjectId
from fastapi.testclient import TestClient

from app.database.client import database
from app.main import app


class InsertOneResult:
    def __init__(self, inserted_id: ObjectId):
        self.inserted_id = inserted_id


class InMemoryUsersCollection:
    def __init__(self):
        self.documents: list[dict] = []

    async def find_one(self, query: dict) -> dict | None:
        for document in self.documents:
            if all(document.get(key) == value for key, value in query.items()):
                return document.copy()
        return None

    async def insert_one(self, document: dict) -> InsertOneResult:
        stored_document = document.copy()
        inserted_id = ObjectId()
        stored_document["_id"] = inserted_id
        self.documents.append(stored_document)
        return InsertOneResult(inserted_id)


class InMemoryDatabase:
    def __init__(self):
        self.users = InMemoryUsersCollection()

    def __getitem__(self, collection_name: str) -> InMemoryUsersCollection:
        return self.users


@pytest.fixture
def client(monkeypatch):
    in_memory_database = InMemoryDatabase()

    async def connect() -> None:
        database.db = in_memory_database

    async def disconnect() -> None:
        database.db = None

    monkeypatch.setattr(database, "connect", connect)
    monkeypatch.setattr(database, "disconnect", disconnect)

    with TestClient(app) as test_client:
        yield test_client

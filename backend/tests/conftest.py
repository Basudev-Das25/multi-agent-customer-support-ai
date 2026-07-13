import pytest
from bson import ObjectId
from fastapi.testclient import TestClient

from app.database.client import database
from app.main import app


class InsertOneResult:
    def __init__(self, inserted_id: ObjectId):
        self.inserted_id = inserted_id


class InMemoryCursor:
    def __init__(self, documents: list[dict]):
        self.documents = documents

    def sort(self, field: str, direction: int) -> "InMemoryCursor":
        self.documents.sort(key=lambda document: document[field], reverse=direction < 0)
        return self

    def limit(self, limit: int) -> "InMemoryCursor":
        self.documents = self.documents[:limit]
        return self

    async def to_list(self, length: int | None = None) -> list[dict]:
        return [document.copy() for document in self.documents[:length]]


class InMemoryCollection:
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

    async def update_one(self, query: dict, update: dict) -> None:
        for document in self.documents:
            if all(document.get(key) == value for key, value in query.items()):
                for field, value in update.get("$set", {}).items():
                    document[field] = value
                for field, operation in update.get("$push", {}).items():
                    document[field].extend(operation["$each"])
                return

    def find(self, query: dict) -> InMemoryCursor:
        return InMemoryCursor(
            [
                document.copy()
                for document in self.documents
                if all(document.get(key) == value for key, value in query.items())
            ]
        )


class InMemoryDatabase:
    def __init__(self):
        self.collections: dict[str, InMemoryCollection] = {}

    def __getitem__(self, collection_name: str) -> InMemoryCollection:
        if collection_name not in self.collections:
            self.collections[collection_name] = InMemoryCollection()
        return self.collections[collection_name]


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

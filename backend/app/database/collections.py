from pymongo.asynchronous.collection import AsyncCollection

from app.core.config import settings
from app.database.client import database


def get_users_collection() -> AsyncCollection:
    return database.get_database()[settings.USERS_COLLECTION]


def get_conversations_collection() -> AsyncCollection:
    return database.get_database()[settings.CONVERSATIONS_COLLECTION]


def get_knowledge_collection() -> AsyncCollection:
    return database.get_database()[settings.KNOWLEDGE_COLLECTION]


def get_analytics_collection() -> AsyncCollection:
    return database.get_database()[settings.ANALYTICS_COLLECTION]


def get_knowledge_chunks_collection() -> AsyncCollection:
    return database.get_database()[settings.KNOWLEDGE_CHUNKS_COLLECTION]

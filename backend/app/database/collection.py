from app.core.config import settings
from app.database.client import database

users_collection = database[settings.USERS_COLLECTION]

conversations_collection = database[settings.CONVERSATIONS_COLLECTION]

knowledge_collection = database[settings.KNOWLEDGE_COLLECTION]

analytics_collection = database[settings.ANALYTICS_COLLECTION]

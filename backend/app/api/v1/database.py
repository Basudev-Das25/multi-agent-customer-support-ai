from fastapi import APIRouter

from app.database.client import database

router = APIRouter()


@router.get("/database")
async def database_status():
    collections = await database.list_collection_names()

    return {
        "connected": True,
        "collections": collections,
    }

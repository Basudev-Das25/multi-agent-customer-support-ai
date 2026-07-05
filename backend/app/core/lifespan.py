from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.logging import logger
from app.database.client import database


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Connecting to MongoDB...")

    await database.connect()

    logger.info("MongoDB Connected")

    yield

    logger.info("Closing MongoDB Connection")

    await database.disconnect()

    logger.info("MongoDB Connection Closed")

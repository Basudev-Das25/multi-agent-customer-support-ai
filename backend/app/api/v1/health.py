from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.database.client import database
from app.schemas.health import HealthResponse

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Check the health of the application",
)
async def health():
    """
    Health check endpoint.
    """

    try:
        if database.client is None:
            raise RuntimeError("Database client is not initialized.")

        await database.client.admin.command("ping")

        return HealthResponse(
            status="healthy",
            service=settings.APP_NAME,
            version=settings.APP_VERSION,
            environment=settings.ENVIRONMENT,
            database="connected",
        )

    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="Service Unavailable: Database connection failed",
        ) from exc

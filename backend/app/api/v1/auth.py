from fastapi import APIRouter, HTTPException, status

from app.core.exception import UserAlreadyExistsError
from app.schemas.auth import RegisterRequest
from app.schemas.user import UserResponse
from app.services.auth_service import register_user

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
async def register(
    request: RegisterRequest,
) -> UserResponse:
    """
    Register a new user.
    """
    try:
        return await register_user(request)

    except UserAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

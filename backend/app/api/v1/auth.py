from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.core.exception import UserAlreadyExistsError
from app.core.security import create_access_token
from app.models.user import UserDocument
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.user import UserResponse
from app.services.auth_service import authenticate_user, register_user

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


@router.post("/login", response_model=TokenResponse, summary="Log in")
async def login(request: LoginRequest) -> TokenResponse:
    """Authenticate a user and issue a JWT access token."""
    user = await authenticate_user(request)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return TokenResponse(
        access_token=create_access_token(
            user_id=user.id or "",
            email=str(user.email),
            role=user.role,
        )
    )


@router.get("/me", response_model=UserResponse, summary="Get current user")
async def read_current_user(
    current_user: Annotated[UserDocument, Depends(get_current_user)],
) -> UserResponse:
    """Return the profile associated with the provided Bearer token."""
    return UserResponse(
        id=current_user.id or "",
        name=current_user.name,
        email=current_user.email,
        role=current_user.role,
        is_active=current_user.is_active,
    )

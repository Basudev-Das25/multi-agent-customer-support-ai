from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import decode_access_token
from app.models.user import UserDocument
from app.services.auth_service import get_user_by_id

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
) -> UserDocument:
    """Resolve the active user represented by a Bearer access token."""
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise unauthorized
    token_data = decode_access_token(credentials.credentials)
    if token_data is None:
        raise unauthorized
    user = await get_user_by_id(token_data.user_id)
    if user is None or not user.is_active:
        raise unauthorized
    return user

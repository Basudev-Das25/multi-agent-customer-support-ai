from pydantic import EmailStr, Field

from app.schemas.base import BaseSchema
from app.schemas.user import BaseUser


class RegisterRequest(BaseUser):
    password: str = Field(
        min_length=8,
        max_length=128,
        description="User password",
    )


class LoginRequest(BaseSchema):
    email: EmailStr
    password: str = Field(
        min_length=8,
        max_length=128,
    )


class TokenResponse(BaseSchema):
    access_token: str
    token_type: str = "bearer"

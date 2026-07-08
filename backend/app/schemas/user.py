from pydantic import EmailStr

from app.schemas.base import BaseSchema


class BaseUser(BaseSchema):
    name: str
    email: EmailStr


class UserResponse(BaseUser):
    id: str
    role: str
    is_active: bool

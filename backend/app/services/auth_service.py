from datetime import UTC, datetime

from app.core.exception import UserAlreadyExistsError
from app.core.security import hash_password
from app.database.collections import get_users_collection
from app.models.user import UserDocument
from app.schemas.auth import RegisterRequest
from app.schemas.user import UserResponse


async def email_exists(email: str) -> bool:
    """
    Check whether a user with the given email already exists.
    """
    users_collection = get_users_collection()
    user = await users_collection.find_one({"email": email})
    return user is not None


def _build_user_document(
    request: RegisterRequest,
    password_hash: str,
) -> UserDocument:
    """
    Build a UserDocument from the registration request.
    """
    now = datetime.now(UTC)

    return UserDocument(
        name=request.name,
        email=request.email,
        password_hash=password_hash,
        role="user",
        is_active=True,
        created_at=now,
        updated_at=now,
    )


async def _create_user(user: UserDocument) -> UserDocument:
    """
    Insert a new user into MongoDB.
    """
    document = user.model_dump(exclude={"id"})

    users_collection = get_users_collection()
    result = await users_collection.insert_one(document)

    user.id = str(result.inserted_id)

    return user


async def register_user(
    request: RegisterRequest,
) -> UserResponse:
    """
    Register a new user.
    """
    if await email_exists(request.email):
        raise UserAlreadyExistsError("Email already registered.")

    password_hash = hash_password(request.password)

    user = _build_user_document(
        request=request,
        password_hash=password_hash,
    )

    created_user = await _create_user(user)

    return UserResponse(
        id=created_user.id,
        name=created_user.name,
        email=created_user.email,
        role=created_user.role,
        is_active=created_user.is_active,
    )

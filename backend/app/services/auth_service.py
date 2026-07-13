from datetime import UTC, datetime

from bson import ObjectId

from app.core.exception import UserAlreadyExistsError
from app.core.security import hash_password, verify_password
from app.database.collections import get_users_collection
from app.models.user import UserDocument
from app.schemas.auth import LoginRequest, RegisterRequest
from app.schemas.user import UserResponse


async def email_exists(email: str) -> bool:
    """
    Check whether a user with the given email already exists.
    """
    users_collection = get_users_collection()
    user = await users_collection.find_one({"email": email})
    return user is not None


def _to_user_document(document: dict) -> UserDocument:
    """Convert a MongoDB user document into the application model."""
    return UserDocument(
        id=str(document["_id"]),
        name=document["name"],
        email=document["email"],
        password_hash=document["password_hash"],
        role=document["role"],
        is_active=document["is_active"],
        created_at=document["created_at"],
        updated_at=document["updated_at"],
    )


async def get_user_by_email(email: str) -> UserDocument | None:
    """Return a user by email, if one exists."""
    users_collection = get_users_collection()
    document = await users_collection.find_one({"email": email})
    return _to_user_document(document) if document else None


async def get_user_by_id(user_id: str) -> UserDocument | None:
    """Return a user by MongoDB object ID, if one exists."""
    if not ObjectId.is_valid(user_id):
        return None
    users_collection = get_users_collection()
    document = await users_collection.find_one({"_id": ObjectId(user_id)})
    return _to_user_document(document) if document else None


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


async def authenticate_user(request: LoginRequest) -> UserDocument | None:
    """Authenticate an active user by email and password."""
    user = await get_user_by_email(str(request.email))
    if user is None or not user.is_active:
        return None
    if not verify_password(request.password, user.password_hash):
        return None
    return user

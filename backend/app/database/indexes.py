"""MongoDB index initialization required by production data invariants."""

from pymongo import ASCENDING, DESCENDING
from pymongo.asynchronous.collection import AsyncCollection

_INDEX_SPECS: list[tuple[str, AsyncCollection, list[tuple[str, int]], dict]] = []


def _register(
    collection: AsyncCollection, keys: list[tuple[str, int]], kwargs: dict
) -> None:
    _INDEX_SPECS.append((collection.name, collection, keys, kwargs))


async def ensure_indexes(
    users: AsyncCollection,
    conversations: AsyncCollection,
    knowledge_documents: AsyncCollection,
    dataset_ingestion_log: AsyncCollection | None = None,
) -> None:
    """Create required MongoDB indexes when they do not already exist."""

    _register(
        users,
        [("email", ASCENDING)],
        {"name": "unique_users_email", "unique": True},
    )
    _register(
        conversations,
        [("user_id", ASCENDING), ("updated_at", DESCENDING)],
        {"name": "conversations_user_id_updated_at"},
    )
    _register(
        knowledge_documents,
        [("user_id", ASCENDING)],
        {"name": "knowledge_documents_user_id"},
    )

    if dataset_ingestion_log is not None:
        _register(
            dataset_ingestion_log,
            [("dataset_name", ASCENDING), ("user_id", ASCENDING)],
            {"name": "dataset_ingestion_log_name_user", "unique": True},
        )

    for _, collection, keys, kwargs in _INDEX_SPECS:
        existing = await collection.index_information()
        target_key = list(keys)

        already_exists = any(
            list(idx.get("key")) == target_key for idx in existing.values()
        )
        if already_exists:
            continue

        await collection.create_index(keys, **kwargs)

from datetime import UTC, datetime
from uuid import uuid4

from bson import ObjectId

from app.database.collections import get_conversations_collection
from app.schemas.chat import ChatMessage, ConversationResponse, ConversationSummary


def _conversation_response(document: dict) -> ConversationResponse:
    return ConversationResponse(
        id=str(document["_id"]),
        title=document["title"],
        messages=[ChatMessage(**message) for message in document["messages"]],
        created_at=document["created_at"],
        updated_at=document["updated_at"],
    )


async def _get_conversation_document(user_id: str, conversation_id: str) -> dict | None:
    if not ObjectId.is_valid(conversation_id):
        return None
    conversations = get_conversations_collection()
    return await conversations.find_one(
        {"_id": ObjectId(conversation_id), "user_id": user_id}
    )


async def get_conversation(
    user_id: str, conversation_id: str
) -> ConversationResponse | None:
    """Return one of a user's conversations."""
    document = await _get_conversation_document(user_id, conversation_id)
    return _conversation_response(document) if document else None


async def list_conversations(user_id: str) -> list[ConversationSummary]:
    """Return a user's conversations ordered by latest activity."""
    conversations = get_conversations_collection()
    cursor = conversations.find({"user_id": user_id}).sort("updated_at", -1).limit(50)
    documents = await cursor.to_list(length=50)
    return [
        ConversationSummary(
            id=str(document["_id"]),
            title=document["title"],
            updated_at=document["updated_at"],
        )
        for document in documents
    ]


def _assistant_response(content: str) -> str:
    """Provide an explicit temporary response until the agent workflow is added."""
    return (
        "Thanks for your message. I have saved it to this conversation. "
        "Specialist agent responses will be enabled in the next AI integration phase."
    )


async def send_message(
    user_id: str, content: str, conversation_id: str | None
) -> ConversationResponse:
    """Persist a user message and the temporary assistant acknowledgement."""
    now = datetime.now(UTC)
    user_message = ChatMessage(
        id=str(uuid4()), role="user", content=content, created_at=now
    )
    assistant_message = ChatMessage(
        id=str(uuid4()),
        role="assistant",
        content=_assistant_response(content),
        created_at=datetime.now(UTC),
    )
    conversations = get_conversations_collection()

    document = (
        await _get_conversation_document(user_id, conversation_id)
        if conversation_id
        else None
    )
    if document is None:
        new_document = {
            "user_id": user_id,
            "title": content[:80],
            "messages": [
                user_message.model_dump(mode="json"),
                assistant_message.model_dump(mode="json"),
            ],
            "created_at": now,
            "updated_at": assistant_message.created_at,
        }
        result = await conversations.insert_one(new_document)
        new_document["_id"] = result.inserted_id
        return _conversation_response(new_document)

    messages = [
        user_message.model_dump(mode="json"),
        assistant_message.model_dump(mode="json"),
    ]
    await conversations.update_one(
        {"_id": document["_id"], "user_id": user_id},
        {
            "$push": {"messages": {"$each": messages}},
            "$set": {"updated_at": assistant_message.created_at},
        },
    )
    document["messages"].extend(messages)
    document["updated_at"] = assistant_message.created_at
    return _conversation_response(document)

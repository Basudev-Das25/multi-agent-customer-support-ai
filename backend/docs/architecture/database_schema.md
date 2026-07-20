# Database Schema

## Overview

The application separates operational data from knowledge data.

| Component | Stores |
|----------|--------|
| MongoDB | Users, Conversations, Messages, Knowledge Document Metadata |
| Local JSONL Storage | Canonical Knowledge Chunk Text |
| FAISS | Vector Embeddings |

MongoDB is **not** used to store chunk text.

---

# Users

Collection:

users

```json
{
    "_id": ObjectId,
    "email": "user@example.com",
    "password_hash": "...",
    "full_name": "John Doe",
    "role": "customer",
    "created_at": "ISO-8601",
    "updated_at": "ISO-8601"
}
```

Indexes

- unique(email)

---

# Conversations

Collection:

conversations

```json
{
    "_id": ObjectId,
    "user_id": ObjectId,
    "title": "React Three Fiber",
    "message_count": 0,
    "created_at": "ISO-8601",
    "updated_at": "ISO-8601",
    "last_message_at": "ISO-8601"
}
```

Indexes

- (user_id, updated_at DESC)

---

# Messages

Collection:

messages

```json
{
    "_id": ObjectId,
    "conversation_id": ObjectId,
    "role": "user",
    "content": "...",
    "agent": "faq",
    "citations": [
        {
            "document_id": "...",
            "chunk_id": "..."
        }
    ],
    "created_at": "ISO-8601"
}
```

Indexes

- (conversation_id, created_at)

---

# Knowledge Documents

Collection:

knowledge_documents

```json
{
    "_id": ObjectId,
    "document_id": "UUID",
    "title": "...",
    "source": "...",
    "file_name": "...",
    "status": "indexed",
    "chunk_count": 0,
    "vector_count": 0,
    "generation": "UUID",
    "content_sha256": "...",
    "created_at": "ISO-8601",
    "updated_at": "ISO-8601"
}
```

Indexes

- unique(document_id)
- status

---

# Ingestion Jobs (Future)

Collection:

ingestion_jobs

```json
{
    "_id": ObjectId,
    "document_id": "...",
    "status": "completed",
    "started_at": "...",
    "completed_at": "...",
    "chunks_created": 0,
    "vectors_created": 0,
    "errors": []
}
```

---

# Storage Responsibility

| Data | MongoDB | JSONL | FAISS |
|------|---------|-------|-------|
| Users | ✓ | | |
| Conversations | ✓ | | |
| Messages | ✓ | | |
| Knowledge Document Metadata | ✓ | | |
| Chunk Text | | ✓ | |
| Embeddings | | | ✓ |

---

# Retrieval Flow

```
User Question
      │
      ▼
EmbeddingService
      │
      ▼
FAISS
      │
(document_id, chunk_id)
      │
      ▼
ChunkStorage
      │
Context Window
      │
      ▼
PromptService
      │
      ▼
LLM
      │
      ▼
ChatService
      │
      ▼
MongoDB (Conversation + Messages + Citations)
```

---

# Design Principles

- MongoDB stores operational data only.
- JSONL is the canonical source for chunk text.
- FAISS stores embeddings only.
- Every piece of data has a single source of truth.
- Retrieval never reads chunk text from MongoDB.
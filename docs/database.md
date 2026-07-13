# Database Design

## Database

customer_support_ai

## Collections

### users

```json
{
    "_id": ObjectId,
    "name": "",
    "email": "",
    "password_hash": "",
    "role": "user",
    "is_active": true,
    "created_at": "",
    "updated_at": ""
}
```

---

### conversations

```json
{
    "_id": ObjectId,
    "user_id": "",
    "session_id": "",
    "messages": [],
    "created_at": "",
    "updated_at": ""
}
```

---

### knowledge_base

Stores uploaded company documents.

---

### analytics

Stores usage metrics.
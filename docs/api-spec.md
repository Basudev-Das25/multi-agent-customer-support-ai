# API Specification

Base URL

```
/api/v1
```

---

## Authentication

POST /auth/register

POST /auth/login

GET /auth/me

POST /auth/logout

---

## Chat

POST /chat

GET /chat/history

DELETE /chat/history

---

## Knowledge Base

POST /knowledge/upload

GET /knowledge

DELETE /knowledge/{id}

---

## Analytics

GET /analytics

---

## Health

GET /health
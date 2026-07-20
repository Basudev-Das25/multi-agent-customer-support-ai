import uuid


def _register_and_login(client) -> str:
    email = f"chat-{uuid.uuid4().hex[:8]}@example.com"
    password = "Password123!"
    registration = client.post(
        "/api/v1/auth/register",
        json={"name": "Chat User", "email": email, "password": password},
    )
    assert registration.status_code == 201
    login = client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    assert login.status_code == 200
    return login.json()["access_token"]


def test_send_message_and_read_conversation(client, monkeypatch):
    async def respond(**_: object) -> str:
        return "I can help with your invoice."

    monkeypatch.setattr("app.services.chat_service.agent_service.respond", respond)

    token = _register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post(
        "/api/v1/chat/messages",
        headers=headers,
        json={"content": "I need help with my invoice."},
    )
    assert response.status_code == 201
    conversation = response.json()
    assert conversation["title"] == "I need help with my invoice."
    assert [message["role"] for message in conversation["messages"]] == [
        "user",
        "assistant",
    ]

    history = client.get("/api/v1/chat/conversations", headers=headers)
    assert history.status_code == 200
    assert history.json()[0]["id"] == conversation["id"]

    detail = client.get(
        f"/api/v1/chat/conversations/{conversation['id']}", headers=headers
    )
    assert detail.status_code == 200
    assert detail.json()["messages"] == conversation["messages"]


def test_chat_requires_authentication(client):
    response = client.post("/api/v1/chat/messages", json={"content": "Hello"})
    assert response.status_code == 401

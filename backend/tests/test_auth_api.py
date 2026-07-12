import uuid


def test_register_user(client):
    unique_email = f"test-{uuid.uuid4().hex[:8]}@example.com"

    response = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Test User",
            "email": unique_email,
            "password": "Password123!",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Test User"
    assert data["email"] == unique_email
    assert data["role"] == "user"
    assert data["is_active"] is True

    assert "password" not in data
    assert "password_hash" not in data


def test_register_duplicate_email(client):
    unique_email = f"duplicate-{uuid.uuid4().hex[:8]}@example.com"

    payload = {
        "name": "Duplicate User",
        "email": unique_email,
        "password": "Password123!",
    }

    first = client.post(
        "/api/v1/auth/register",
        json=payload,
    )

    assert first.status_code == 201

    second = client.post(
        "/api/v1/auth/register",
        json=payload,
    )

    assert second.status_code == 409
    assert second.json()["detail"] == "Email already registered."

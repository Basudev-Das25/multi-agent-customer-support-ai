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


def test_login_and_get_current_user(client):
    email = f"login-{uuid.uuid4().hex[:8]}@example.com"
    password = "Password123!"

    registration = client.post(
        "/api/v1/auth/register",
        json={"name": "Login User", "email": email, "password": password},
    )
    assert registration.status_code == 201

    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login.status_code == 200
    assert login.json()["token_type"] == "bearer"

    profile = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {login.json()['access_token']}"},
    )
    assert profile.status_code == 200
    assert profile.json()["email"] == email
    assert profile.json()["name"] == "Login User"


def test_login_rejects_invalid_password(client):
    email = f"invalid-login-{uuid.uuid4().hex[:8]}@example.com"
    registration = client.post(
        "/api/v1/auth/register",
        json={"name": "Invalid Login", "email": email, "password": "Password123!"},
    )
    assert registration.status_code == 201

    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "WrongPassword123!"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password."

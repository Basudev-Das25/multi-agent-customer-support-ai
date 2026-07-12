from app.core.security import create_access_token, decode_access_token


def test_access_token_round_trip():
    token = create_access_token(
        user_id="123",
        email="user@example.com",
        role="user",
    )

    payload = decode_access_token(token)

    assert payload is not None
    assert payload.user_id == "123"
    assert payload.email == "user@example.com"
    assert payload.role == "user"


def test_invalid_access_token_returns_none():
    assert decode_access_token("not-a-valid-token") is None

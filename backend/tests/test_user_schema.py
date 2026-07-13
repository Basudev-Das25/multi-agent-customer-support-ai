import pytest
from pydantic import ValidationError

from app.schemas.auth import RegisterRequest


def test_valid_register_request():
    user = RegisterRequest(
        name="Basudev",
        email="basudev@example.com",
        password="Password123!",
    )

    assert user.email == "basudev@example.com"


def test_invalid_email():
    with pytest.raises(ValidationError):
        RegisterRequest(
            name="Basudev",
            email="invalid-email",
            password="Password123!",
        )


def test_short_password():
    with pytest.raises(ValidationError):
        RegisterRequest(
            name="Basudev",
            email="basudev@example.com",
            password="123",
        )

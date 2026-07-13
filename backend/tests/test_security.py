from app.core.security import hash_password, verify_password


def test_password_hashing():
    password = "MySecurePassword123!"

    hashed_password = hash_password(password)

    # Hash should not equal original password
    assert hashed_password != password

    # Correct password should verify
    assert verify_password(password, hashed_password) is True

    # Incorrect password should fail
    assert verify_password("WrongPassword", hashed_password) is False

class AppException(Exception):
    """Base application exception."""


class UserAlreadyExistsError(AppException):
    """Raised when a user tries to register with an existing email."""


class InvalidCredentialsError(AppException):
    """Raised when login credentials are invalid."""

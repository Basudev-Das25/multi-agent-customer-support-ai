class AppException(Exception):
    """Base application exception."""


class UserAlreadyExistsError(AppException):
    """Raised when a user tries to register with an existing email."""


class ConversationNotFoundError(AppException):
    """Raised when a requested conversation does not exist."""

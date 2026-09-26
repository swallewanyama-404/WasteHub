class WasteHubException(Exception):
    """Base exception for WasteHub application errors."""

    def __init__(
        self,
        message: str,
        status_code: int = 400,
    ):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class ResourceNotFoundException(WasteHubException):
    """Raised when a requested resource does not exist."""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(
            message=message,
            status_code=404,
        )


class UnauthorizedException(WasteHubException):
    """Raised when authentication is required or invalid."""

    def __init__(self, message: str = "Unauthorized"):
        super().__init__(
            message=message,
            status_code=401,
        )


class ForbiddenException(WasteHubException):
    """Raised when a user does not have permission."""

    def __init__(self, message: str = "Forbidden"):
        super().__init__(
            message=message,
            status_code=403,
        )

class ConflictException(WasteHubException):
    """Raised when a request conflicts with existing data."""

    def __init__(
        self,
        message: str = "Resource already exists",
    ):
        super().__init__(
            message=message,
            status_code=409,
        )     
        
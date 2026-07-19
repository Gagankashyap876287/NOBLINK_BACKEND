class AppException(Exception):
    """Base application error mapped to an HTTP response."""

    def __init__(
        self,
        message: str,
        status_code: int = 400,
        details: object | None = None,
    ):
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(message)


class BadRequestError(AppException):
    def __init__(self, message: str, details: object | None = None):
        super().__init__(message=message, status_code=400, details=details)


class NotFoundError(AppException):
    def __init__(self, message: str = "Resource not found."):
        super().__init__(message=message, status_code=404)

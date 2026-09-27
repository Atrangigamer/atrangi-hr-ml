"""Typed failures that may safely cross the API boundary."""


class ServiceError(Exception):
    """An expected failure with a public status, stable code and safe message."""

    def __init__(self, status: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status, self.code, self.message = status, code, message


class InvalidPDF(ServiceError):
    """A PDF that cannot be processed as a bounded, text-bearing document."""

    def __init__(self, message: str) -> None:
        super().__init__(400, "invalid_pdf", message)

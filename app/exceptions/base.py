from __future__ import annotations


class AppException(Exception):
    status_code = 500
    default_detail = "Internal Server Error"

    def __init__(self, detail: str | None = None) -> None:
        self.detail = detail or self.default_detail
        super().__init__(self.detail)


class BadRequestError(AppException):
    status_code = 400
    default_detail = "Bad request"


class NotFoundError(AppException):
    status_code = 404
    default_detail = "Not found"


class ConflictError(AppException):
    status_code = 409
    default_detail = "Conflict"

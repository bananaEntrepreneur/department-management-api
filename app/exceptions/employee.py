from __future__ import annotations

from app.exceptions.base import NotFoundError


class EmployeeDepartmentNotFoundError(NotFoundError):
    default_detail = "Department not found"

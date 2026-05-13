from app.exceptions.base import AppException, BadRequestError, ConflictError, NotFoundError
from app.exceptions.department import (
    DepartmentAlreadyExistsInParentError,
    DepartmentCannotBeItsOwnParentError,
    DepartmentCannotBeMovedIntoItsOwnSubtreeError,
    DepartmentCannotBeReassignedToItselfError,
    DepartmentNotFoundError,
    ParentDepartmentNotFoundError,
    ReassignDepartmentNotFoundError,
    ReassignToDepartmentRequiredError,
)
from app.exceptions.employee import EmployeeDepartmentNotFoundError
from app.exceptions.handlers import register_exception_handlers

__all__ = [
    "AppException",
    "BadRequestError",
    "ConflictError",
    "NotFoundError",
    "DepartmentAlreadyExistsInParentError",
    "DepartmentCannotBeItsOwnParentError",
    "DepartmentCannotBeMovedIntoItsOwnSubtreeError",
    "DepartmentCannotBeReassignedToItselfError",
    "DepartmentNotFoundError",
    "ParentDepartmentNotFoundError",
    "ReassignDepartmentNotFoundError",
    "ReassignToDepartmentRequiredError",
    "EmployeeDepartmentNotFoundError",
    "register_exception_handlers",
]

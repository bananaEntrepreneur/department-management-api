from __future__ import annotations

from app.exceptions.base import BadRequestError, ConflictError, NotFoundError


class DepartmentNotFoundError(NotFoundError):
    default_detail = "Department not found"


class ParentDepartmentNotFoundError(NotFoundError):
    default_detail = "Parent department not found"


class DepartmentAlreadyExistsInParentError(ConflictError):
    default_detail = "Department with this name already exists in this parent"


class DepartmentCannotBeItsOwnParentError(ConflictError):
    default_detail = "Department cannot be its own parent"


class DepartmentCannotBeMovedIntoItsOwnSubtreeError(ConflictError):
    default_detail = "Department cannot be moved into its own subtree"


class ReassignToDepartmentRequiredError(BadRequestError):
    default_detail = "reassign_to_department_id is required when mode=reassign"


class DepartmentCannotBeReassignedToItselfError(BadRequestError):
    default_detail = "Department cannot be reassigned to itself"


class ReassignDepartmentNotFoundError(NotFoundError):
    default_detail = "Reassign department not found"

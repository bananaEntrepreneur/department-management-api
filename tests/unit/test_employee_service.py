from __future__ import annotations

from datetime import date
from unittest.mock import AsyncMock

import pytest
from pydantic import ValidationError

from app.exceptions.employee import EmployeeDepartmentNotFoundError
from app.models.department import Department
from app.models.employee import Employee
from app.schemas.employee import AddEmployeeRequest
from app.services.employee import EmployeeService


@pytest.mark.asyncio
async def test_add_employee_creates_employee_for_existing_department() -> None:
    service = EmployeeService(db=object())
    service.department_repository = AsyncMock()
    service.employee_repository = AsyncMock()

    service.department_repository.get_by_id.return_value = Department(
        id=1,
        name="Operations",
        parent_id=None,
    )
    created_employee = Employee(
        id=1,
        department_id=1,
        full_name="Ada Lovelace",
        position="Analyst",
        hired_at=date(2026, 5, 1),
    )
    service.employee_repository.create.return_value = created_employee

    result = await service.add_employee(
        department_id=1,
        full_name="Ada Lovelace",
        position="Analyst",
        hired_at=date(2026, 5, 1),
    )

    assert result is created_employee
    service.department_repository.get_by_id.assert_awaited_once_with(1)
    service.employee_repository.create.assert_awaited_once_with(
        department_id=1,
        full_name="Ada Lovelace",
        position="Analyst",
        hired_at=date(2026, 5, 1),
    )


def test_add_employee_request_trims_full_name_and_accepts_single_character() -> None:
    request = AddEmployeeRequest(
        full_name="  A  ",
        position="  Analyst  ",
        hired_at=None,
    )

    assert request.full_name == "A"
    assert request.position == "Analyst"


def test_add_employee_request_rejects_empty_position() -> None:
    with pytest.raises(ValidationError):
        AddEmployeeRequest(
            full_name="Ada Lovelace",
            position="   ",
            hired_at=None,
        )


def test_add_employee_request_rejects_too_long_position() -> None:
    with pytest.raises(ValidationError):
        AddEmployeeRequest(
            full_name="Ada Lovelace",
            position="A" * 201,
            hired_at=None,
        )


@pytest.mark.asyncio
async def test_add_employee_rejects_missing_department() -> None:
    service = EmployeeService(db=object())
    service.department_repository = AsyncMock()
    service.employee_repository = AsyncMock()
    service.department_repository.get_by_id.return_value = None

    with pytest.raises(EmployeeDepartmentNotFoundError) as exc_info:
        await service.add_employee(
            department_id=999,
            full_name="Ada Lovelace",
            position="Analyst",
            hired_at=None,
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Department not found"
    service.department_repository.get_by_id.assert_awaited_once_with(999)
    service.employee_repository.create.assert_not_awaited()

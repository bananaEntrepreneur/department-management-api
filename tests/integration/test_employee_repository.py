from __future__ import annotations

from datetime import date

import pytest

from app.repositories.department import DepartmentRepository
from app.models.employee import Employee
from app.repositories.employee import EmployeeRepository


@pytest.mark.asyncio
async def test_repository_creates_employee(sqlite_session_factory) -> None:
    async with sqlite_session_factory() as session:
        department_repository = DepartmentRepository(session)
        department = await department_repository.create(
            name="Operations",
            parent_id=None,
        )
        repository = EmployeeRepository(session)

        employee = await repository.create(
            department_id=department.id,
            full_name="Ada Lovelace",
            position="Analyst",
            hired_at=date(2026, 5, 1),
        )

        persisted_employee = await session.get(Employee, employee.id)

        assert persisted_employee is not None
        assert persisted_employee.id == employee.id
        assert persisted_employee.department_id == department.id
        assert persisted_employee.full_name == "Ada Lovelace"
        assert persisted_employee.position == "Analyst"
        assert persisted_employee.hired_at == date(2026, 5, 1)

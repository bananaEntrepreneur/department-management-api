from __future__ import annotations

from datetime import date

import pytest

from app.models.department import Department
from app.repositories.department import DepartmentRepository
from app.repositories.employee import EmployeeRepository


@pytest.mark.asyncio
async def test_repository_creates_and_fetches_department(sqlite_session_factory) -> None:
    async with sqlite_session_factory() as session:
        repository = DepartmentRepository(session)

        created_department = await repository.create(
            name="Operations",
            parent_id=None,
        )

        fetched_department = await repository.get_by_id(created_department.id)

        assert fetched_department is not None
        assert fetched_department.id == created_department.id
        assert fetched_department.name == "Operations"
        assert fetched_department.parent_id is None
        assert isinstance(fetched_department, Department)


@pytest.mark.asyncio
async def test_repository_returns_children_in_stable_order(sqlite_session_factory) -> None:
    async with sqlite_session_factory() as session:
        repository = DepartmentRepository(session)

        parent = await repository.create(name="Operations", parent_id=None)
        first_child = await repository.create(name="Alpha", parent_id=parent.id)
        second_child = await repository.create(name="Beta", parent_id=parent.id)

        children = await repository.get_children(parent.id)

        assert [child.id for child in children] == [first_child.id, second_child.id]
        assert [child.name for child in children] == ["Alpha", "Beta"]
        assert all(child.parent_id == parent.id for child in children)


@pytest.mark.asyncio
async def test_repository_finds_department_by_parent_and_name(sqlite_session_factory) -> None:
    async with sqlite_session_factory() as session:
        repository = DepartmentRepository(session)

        root = await repository.create(name="Operations", parent_id=None)
        child = await repository.create(name="Backend", parent_id=root.id)

        found_root = await repository.get_by_parent_and_name(parent_id=None, name="Operations")
        found_child = await repository.get_by_parent_and_name(
            parent_id=root.id,
            name="Backend",
        )
        missing_department = await repository.get_by_parent_and_name(
            parent_id=root.id,
            name="Platform",
        )

        assert found_root is not None
        assert found_root.id == root.id
        assert found_child is not None
        assert found_child.id == child.id
        assert missing_department is None


@pytest.mark.asyncio
async def test_repository_returns_employees_in_stable_order(sqlite_session_factory) -> None:
    async with sqlite_session_factory() as session:
        department_repository = DepartmentRepository(session)
        department = await department_repository.create(name="Operations", parent_id=None)

        employee_repository = EmployeeRepository(session)

        second_employee = await employee_repository.create(
            department_id=department.id,
            full_name="Alice Smith",
            position="Lead",
            hired_at=date(2026, 5, 1),
        )
        first_employee = await employee_repository.create(
            department_id=department.id,
            full_name="Charlie Brown",
            position="Analyst",
            hired_at=date(2026, 5, 3),
        )

        employees = await department_repository.get_employees(department.id)

        assert [employee.id for employee in employees] == [
            second_employee.id,
            first_employee.id,
        ]
        assert [employee.full_name for employee in employees] == [
            "Alice Smith",
            "Charlie Brown",
        ]
        assert all(employee.department_id == department.id for employee in employees)


@pytest.mark.asyncio
async def test_repository_saves_department_changes(sqlite_session_factory) -> None:
    async with sqlite_session_factory() as session:
        repository = DepartmentRepository(session)

        department = await repository.create(name="Operations", parent_id=None)
        department.name = "Ops"
        department.parent_id = None

        saved_department = await repository.save(department)

        assert saved_department.id == department.id
        assert saved_department.name == "Ops"
        assert saved_department.parent_id is None


@pytest.mark.asyncio
async def test_repository_returns_descendants_in_depth_first_order(sqlite_session_factory) -> None:
    async with sqlite_session_factory() as session:
        repository = DepartmentRepository(session)

        root = await repository.create(name="Operations", parent_id=None)
        child = await repository.create(name="Payroll", parent_id=root.id)
        grandchild = await repository.create(name="Support", parent_id=child.id)

        descendants = await repository.get_descendants(root.id)

        assert [department.id for department in descendants] == [child.id, grandchild.id]
        assert [department.name for department in descendants] == ["Payroll", "Support"]


@pytest.mark.asyncio
async def test_repository_deletes_department(sqlite_session_factory) -> None:
    async with sqlite_session_factory() as session:
        repository = DepartmentRepository(session)

        department = await repository.create(name="Operations", parent_id=None)
        await repository.delete(department)

        fetched_department = await repository.get_by_id(department.id)

        assert fetched_department is None

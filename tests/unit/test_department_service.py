from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.models.department import Department
from app.models.employee import Employee
from app.services.department import DepartmentService


@pytest.mark.asyncio
async def test_add_department_creates_root_department() -> None:
    service = DepartmentService(db=object())
    service.repository = AsyncMock()

    created_department = Department(id=1, name="Operations", parent_id=None)
    service.repository.create.return_value = created_department

    result = await service.add_department(name="Operations", parent_id=None)

    assert result is created_department
    service.repository.get_by_id.assert_not_awaited()
    service.repository.create.assert_awaited_once_with(
        name="Operations",
        parent_id=None,
    )


@pytest.mark.asyncio
async def test_add_department_requires_existing_parent() -> None:
    service = DepartmentService(db=object())
    service.repository = AsyncMock()
    service.repository.get_by_id.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        await service.add_department(name="Finance", parent_id=99)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Parent department not found"
    service.repository.get_by_id.assert_awaited_once_with(99)
    service.repository.create.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_department_details_builds_recursive_tree() -> None:
    service = DepartmentService(db=object())
    service.repository = AsyncMock()

    root = Department(
        id=1,
        name="Operations",
        parent_id=None,
        created_at=datetime.now(timezone.utc),
    )
    child = Department(
        id=2,
        name="Payroll",
        parent_id=1,
        created_at=datetime.now(timezone.utc),
    )
    grandchild = Department(
        id=3,
        name="Support",
        parent_id=2,
        created_at=datetime.now(timezone.utc),
    )

    service.repository.get_by_id.return_value = root
    service.repository.get_children.side_effect = [
        [child],
        [grandchild],
        [],
    ]
    service.repository.get_employees.side_effect = [
        [
            Employee(
                id=10,
                department_id=1,
                full_name="Alice",
                position="Lead",
                created_at=datetime.now(timezone.utc),
            )
        ],
        [
            Employee(
                id=11,
                department_id=2,
                full_name="Bob",
                position="Analyst",
                created_at=datetime.now(timezone.utc),
            )
        ],
        [
            Employee(
                id=12,
                department_id=3,
                full_name="Cara",
                position="Specialist",
                created_at=datetime.now(timezone.utc),
            )
        ],
    ]

    result = await service.get_department_details(
        department_id=1,
        depth=2,
        include_employees=True,
    )

    assert result.department.id == 1
    assert len(result.employees) == 1
    assert result.employees[0].full_name == "Alice"
    assert len(result.children) == 1
    assert result.children[0].department.id == 2
    assert len(result.children[0].employees) == 1
    assert result.children[0].employees[0].full_name == "Bob"
    assert len(result.children[0].children) == 1
    assert result.children[0].children[0].department.id == 3
    assert result.children[0].children[0].employees[0].full_name == "Cara"


@pytest.mark.asyncio
async def test_get_department_details_rejects_missing_department() -> None:
    service = DepartmentService(db=object())
    service.repository = AsyncMock()
    service.repository.get_by_id.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        await service.get_department_details(
            department_id=404,
            depth=1,
            include_employees=True,
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Department not found"


@pytest.mark.asyncio
async def test_update_department_changes_name_and_parent() -> None:
    service = DepartmentService(db=object())
    service.repository = AsyncMock()

    root = Department(
        id=1,
        name="Operations",
        parent_id=None,
        created_at=datetime.now(timezone.utc),
    )
    parent = Department(
        id=2,
        name="Corporate",
        parent_id=None,
        created_at=datetime.now(timezone.utc),
    )

    service.repository.get_by_id.side_effect = [root, parent]
    service.repository.save.side_effect = lambda department: department

    from app.schemas.department import DepartmentUpdate

    result = await service.update_department(
        department_id=1,
        payload=DepartmentUpdate(name="Ops", parent_id=2),
    )

    assert result.name == "Ops"
    assert result.parent_id == 2
    assert service.repository.get_by_id.await_count == 2
    service.repository.save.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_department_rejects_self_parent() -> None:
    service = DepartmentService(db=object())
    service.repository = AsyncMock()
    department = Department(
        id=1,
        name="Operations",
        parent_id=None,
        created_at=datetime.now(timezone.utc),
    )
    service.repository.get_by_id.return_value = department

    from app.schemas.department import DepartmentUpdate

    with pytest.raises(HTTPException) as exc_info:
        await service.update_department(
            department_id=1,
            payload=DepartmentUpdate(parent_id=1),
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Department cannot be its own parent"
    service.repository.save.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_department_rejects_moving_into_own_subtree() -> None:
    service = DepartmentService(db=object())
    service.repository = AsyncMock()

    root = Department(
        id=1,
        name="Operations",
        parent_id=None,
        created_at=datetime.now(timezone.utc),
    )
    child = Department(
        id=2,
        name="Payroll",
        parent_id=1,
        created_at=datetime.now(timezone.utc),
    )
    grandchild = Department(
        id=3,
        name="Support",
        parent_id=2,
        created_at=datetime.now(timezone.utc),
    )

    service.repository.get_by_id.side_effect = [root, grandchild, child, root]

    from app.schemas.department import DepartmentUpdate

    with pytest.raises(HTTPException) as exc_info:
        await service.update_department(
            department_id=1,
            payload=DepartmentUpdate(parent_id=3),
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Department cannot be moved into its own subtree"
    service.repository.save.assert_not_awaited()

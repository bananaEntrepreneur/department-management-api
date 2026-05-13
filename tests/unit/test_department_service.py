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
    service.repository.get_by_parent_and_name.return_value = None
    service.repository.create.return_value = created_department

    result = await service.add_department(name="Operations", parent_id=None)

    assert result is created_department
    service.repository.get_by_id.assert_not_awaited()
    service.repository.get_by_parent_and_name.assert_awaited_once_with(
        parent_id=None,
        name="Operations",
        exclude_department_id=None,
    )
    service.repository.create.assert_awaited_once_with(
        name="Operations",
        parent_id=None,
    )


@pytest.mark.asyncio
async def test_add_department_trims_name_before_creating() -> None:
    service = DepartmentService(db=object())
    service.repository = AsyncMock()
    service.repository.get_by_parent_and_name.return_value = None
    service.repository.create.return_value = Department(
        id=1,
        name="Operations",
        parent_id=None,
    )

    result = await service.add_department(name="  Operations  ", parent_id=None)

    assert result.name == "Operations"
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
async def test_add_department_rejects_duplicate_name_in_same_parent() -> None:
    service = DepartmentService(db=object())
    service.repository = AsyncMock()

    service.repository.get_by_parent_and_name.return_value = Department(
        id=2,
        name="Operations",
        parent_id=None,
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.add_department(name="Operations", parent_id=None)

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == "Department with this name already exists in this parent"
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
    service.repository.get_by_parent_and_name.return_value = None
    service.repository.save.side_effect = lambda department: department

    from app.schemas.department import DepartmentUpdate

    result = await service.update_department(
        department_id=1,
        payload=DepartmentUpdate(name="Ops", parent_id=2),
    )

    assert result.name == "Ops"
    assert result.parent_id == 2
    assert service.repository.get_by_id.await_count == 2
    service.repository.get_by_parent_and_name.assert_awaited_once_with(
        parent_id=2,
        name="Ops",
        exclude_department_id=1,
    )
    service.repository.save.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_department_rejects_duplicate_name_in_same_parent() -> None:
    service = DepartmentService(db=object())
    service.repository = AsyncMock()

    department = Department(
        id=1,
        name="Operations",
        parent_id=None,
        created_at=datetime.now(timezone.utc),
    )
    service.repository.get_by_id.return_value = department
    service.repository.get_by_parent_and_name.return_value = Department(
        id=2,
        name="Finance",
        parent_id=None,
        created_at=datetime.now(timezone.utc),
    )

    from app.schemas.department import DepartmentUpdate

    with pytest.raises(HTTPException) as exc_info:
        await service.update_department(
            department_id=1,
            payload=DepartmentUpdate(name="Finance"),
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == "Department with this name already exists in this parent"
    service.repository.save.assert_not_awaited()


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

    assert exc_info.value.status_code == 409
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

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == "Department cannot be moved into its own subtree"
    service.repository.save.assert_not_awaited()


@pytest.mark.asyncio
async def test_delete_department_cascade_deletes_subtree_and_employees() -> None:
    service = DepartmentService(db=object())
    service.repository = AsyncMock()
    service.employee_repository = AsyncMock()

    department = Department(
        id=1,
        name="Operations",
        parent_id=None,
        created_at=datetime.now(timezone.utc),
    )

    service.repository.get_by_id.return_value = department

    await service.delete_department(
        department_id=1,
        mode="cascade",
    )

    service.repository.delete.assert_awaited_once_with(department)
    service.employee_repository.delete_by_department_id.assert_not_awaited()


@pytest.mark.asyncio
async def test_delete_department_reassign_moves_employees_and_promotes_children() -> None:
    service = DepartmentService(db=object())
    service.repository = AsyncMock()
    service.employee_repository = AsyncMock()

    department = Department(
        id=2,
        name="Payroll",
        parent_id=1,
        created_at=datetime.now(timezone.utc),
    )
    target = Department(
        id=4,
        name="Finance",
        parent_id=None,
        created_at=datetime.now(timezone.utc),
    )
    child = Department(
        id=3,
        name="Support",
        parent_id=2,
        created_at=datetime.now(timezone.utc),
    )

    service.repository.get_by_id.side_effect = [department, target]
    service.repository.get_children.return_value = [child]
    service.repository.save.side_effect = lambda item: item

    await service.delete_department(
        department_id=2,
        mode="reassign",
        reassign_to_department_id=4,
    )

    service.employee_repository.reassign_department.assert_awaited_once_with(
        source_department_id=2,
        target_department_id=4,
    )
    assert child.parent_id == 1
    service.repository.save.assert_awaited_once()
    service.repository.delete.assert_awaited_once_with(department)


@pytest.mark.asyncio
async def test_delete_department_reassign_requires_target_department() -> None:
    service = DepartmentService(db=object())
    service.repository = AsyncMock()
    service.employee_repository = AsyncMock()

    department = Department(
        id=1,
        name="Operations",
        parent_id=None,
        created_at=datetime.now(timezone.utc),
    )
    service.repository.get_by_id.return_value = department

    with pytest.raises(HTTPException) as exc_info:
        await service.delete_department(
            department_id=1,
            mode="reassign",
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "reassign_to_department_id is required when mode=reassign"
    service.repository.delete.assert_not_awaited()

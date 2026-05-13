from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.models.department import Department
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

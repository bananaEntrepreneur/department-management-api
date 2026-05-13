from __future__ import annotations

import pytest

from app.models.department import Department
from app.repositories.department import DepartmentRepository


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

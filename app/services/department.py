from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.department import Department
from app.repositories.department import DepartmentRepository


class DepartmentService:
    def __init__(self, db: AsyncSession) -> None:
        self.repository = DepartmentRepository(db)

    async def add_department(self, name: str, parent_id: int | None) -> Department:
        if parent_id is not None:
            parent = await self.repository.get_by_id(parent_id)
            if parent is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Parent department not found",
                )

        return await self.repository.create(name=name, parent_id=parent_id)

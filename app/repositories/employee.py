from __future__ import annotations

from datetime import date

from sqlalchemy import delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.employee import Employee


class EmployeeRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        department_id: int,
        full_name: str,
        position: str,
        hired_at: date | None,
    ) -> Employee:
        employee = Employee(
            department_id=department_id,
            full_name=full_name,
            position=position,
            hired_at=hired_at,
        )
        self.db.add(employee)
        await self.db.commit()
        await self.db.refresh(employee)
        return employee

    async def reassign_department(self, source_department_id: int, target_department_id: int) -> None:
        await self.db.execute(
            update(Employee)
            .where(Employee.department_id == source_department_id)
            .values(department_id=target_department_id)
        )
        await self.db.commit()

    async def delete_by_department_id(self, department_id: int) -> None:
        await self.db.execute(delete(Employee).where(Employee.department_id == department_id))
        await self.db.commit()

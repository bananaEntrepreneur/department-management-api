from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.department import Department
from app.models.employee import Employee


class DepartmentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, name: str, parent_id: int | None) -> Department:
        department = Department(name=name, parent_id=parent_id)
        self.db.add(department)
        await self.db.commit()
        await self.db.refresh(department)
        return department

    async def get_by_id(self, department_id: int) -> Department | None:
        result = await self.db.execute(
            select(Department).where(Department.id == department_id)
        )
        return result.scalar_one_or_none()

    async def get_employees(self, department_id: int) -> list[Employee]:
        result = await self.db.execute(
            select(Employee)
            .where(Employee.department_id == department_id)
            .order_by(Employee.created_at, Employee.full_name, Employee.id)
        )
        return list(result.scalars().all())

    async def get_children(self, parent_id: int) -> list[Department]:
        result = await self.db.execute(
            select(Department)
            .where(Department.parent_id == parent_id)
            .order_by(Department.created_at, Department.name, Department.id)
        )
        return list(result.scalars().all())

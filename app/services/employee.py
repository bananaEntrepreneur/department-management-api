from __future__ import annotations

from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.employee import EmployeeDepartmentNotFoundError
from app.models.employee import Employee
from app.repositories.department import DepartmentRepository
from app.repositories.employee import EmployeeRepository


class EmployeeService:
    def __init__(self, db: AsyncSession) -> None:
        self.department_repository = DepartmentRepository(db)
        self.employee_repository = EmployeeRepository(db)

    async def add_employee(
        self,
        department_id: int,
        full_name: str,
        position: str,
        hired_at: date | None,
    ) -> Employee:
        department = await self.department_repository.get_by_id(department_id)
        if department is None:
            raise EmployeeDepartmentNotFoundError()

        return await self.employee_repository.create(
            department_id=department_id,
            full_name=full_name,
            position=position,
            hired_at=hired_at,
        )

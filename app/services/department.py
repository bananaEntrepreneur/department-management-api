from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.department import Department
from app.repositories.department import DepartmentRepository
from app.schemas.department import DepartmentDTO, DepartmentDetailsDTO
from app.schemas.employee import EmployeeDTO


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

    async def get_department_details(
        self,
        department_id: int,
        depth: int = 1,
        include_employees: bool = True,
    ) -> DepartmentDetailsDTO:
        department = await self.repository.get_by_id(department_id)
        if department is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Department not found",
            )

        return await self._build_department_details(
            department=department,
            depth=depth,
            include_employees=include_employees,
        )

    async def _build_department_details(
        self,
        department: Department,
        depth: int,
        include_employees: bool,
    ) -> DepartmentDetailsDTO:
        employees = []
        if include_employees:
            employees = [
                EmployeeDTO.model_validate(employee)
                for employee in await self.repository.get_employees(department.id)
            ]

        children: list[DepartmentDetailsDTO] = []
        if depth > 0:
            for child in await self.repository.get_children(department.id):
                children.append(
                    await self._build_department_details(
                        department=child,
                        depth=depth - 1,
                        include_employees=include_employees,
                    )
                )

        return DepartmentDetailsDTO(
            department=DepartmentDTO.model_validate(department),
            employees=employees,
            children=children,
        )

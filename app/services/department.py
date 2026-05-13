from __future__ import annotations

from typing import Literal

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.department import (
    DepartmentAlreadyExistsInParentError,
    DepartmentCannotBeItsOwnParentError,
    DepartmentCannotBeMovedIntoItsOwnSubtreeError,
    DepartmentCannotBeReassignedToItselfError,
    DepartmentNotFoundError,
    ParentDepartmentNotFoundError,
    ReassignDepartmentNotFoundError,
    ReassignToDepartmentRequiredError,
)
from app.models.department import Department
from app.repositories.department import DepartmentRepository
from app.repositories.employee import EmployeeRepository
from app.schemas.department import DepartmentDTO, DepartmentDetailsDTO, DepartmentUpdate
from app.schemas.employee import EmployeeDTO


class DepartmentService:
    def __init__(self, db: AsyncSession) -> None:
        self.repository = DepartmentRepository(db)
        self.employee_repository = EmployeeRepository(db)

    async def add_department(self, name: str, parent_id: int | None) -> Department:
        name = name.strip()

        if parent_id is not None:
            parent = await self.repository.get_by_id(parent_id)
            if parent is None:
                raise ParentDepartmentNotFoundError()

        await self._ensure_department_name_is_available(
            name=name,
            parent_id=parent_id,
        )

        return await self.repository.create(name=name, parent_id=parent_id)

    async def update_department(
        self,
        department_id: int,
        payload: DepartmentUpdate,
    ) -> Department:
        department = await self.repository.get_by_id(department_id)
        if department is None:
            raise DepartmentNotFoundError()

        if "parent_id" in payload.model_fields_set:
            parent_id = payload.parent_id
            if parent_id == department_id:
                raise DepartmentCannotBeItsOwnParentError()

            if parent_id is not None:
                parent = await self.repository.get_by_id(parent_id)
                if parent is None:
                    raise ParentDepartmentNotFoundError()

                visited_ids: set[int] = set()
                current_parent = parent
                while current_parent is not None:
                    if current_parent.id == department_id:
                        raise DepartmentCannotBeMovedIntoItsOwnSubtreeError()
                    if current_parent.parent_id is None:
                        break
                    if current_parent.id in visited_ids:
                        break
                    visited_ids.add(current_parent.id)
                    current_parent = await self.repository.get_by_id(current_parent.parent_id)

            department.parent_id = parent_id

        if "name" in payload.model_fields_set and payload.name is not None:
            department.name = payload.name.strip()

        await self._ensure_department_name_is_available(
            name=department.name,
            parent_id=department.parent_id,
            exclude_department_id=department.id,
        )

        return await self.repository.save(department)

    async def delete_department(
        self,
        department_id: int,
        mode: Literal["cascade", "reassign"],
        reassign_to_department_id: int | None = None,
    ) -> None:
        department = await self.repository.get_by_id(department_id)
        if department is None:
            raise DepartmentNotFoundError()

        if mode == "cascade":
            await self.repository.delete(department)
            return

        if reassign_to_department_id is None:
            raise ReassignToDepartmentRequiredError()

        if reassign_to_department_id == department_id:
            raise DepartmentCannotBeReassignedToItselfError()

        target_department = await self.repository.get_by_id(reassign_to_department_id)
        if target_department is None:
            raise ReassignDepartmentNotFoundError()

        await self.employee_repository.reassign_department(
            source_department_id=department.id,
            target_department_id=target_department.id,
        )

        for child in await self.repository.get_children(department.id):
            child.parent_id = department.parent_id
            await self.repository.save(child)

        await self.repository.delete(department)

    async def get_department_details(
        self,
        department_id: int,
        depth: int = 1,
        include_employees: bool = True,
    ) -> DepartmentDetailsDTO:
        department = await self.repository.get_by_id(department_id)
        if department is None:
            raise DepartmentNotFoundError()

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

    async def _ensure_department_name_is_available(
        self,
        name: str,
        parent_id: int | None,
        exclude_department_id: int | None = None,
    ) -> None:
        existing_department = await self.repository.get_by_parent_and_name(
            parent_id=parent_id,
            name=name,
            exclude_department_id=exclude_department_id,
        )
        if existing_department is not None:
            raise DepartmentAlreadyExistsInParentError()

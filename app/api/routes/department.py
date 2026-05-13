from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query
from starlette import status

from app.core.dependencies import get_department_service, get_employee_service
from app.schemas.employee import AddEmployeeRequest, AddEmployeeResponse, EmployeeDTO
from app.schemas.department import DepartmentCreate, DepartmentDTO, DepartmentDetailsDTO, DepartmentUpdate
from app.services.department import DepartmentService
from app.services.employee import EmployeeService

departments_router = APIRouter(prefix="/departments", tags=["Departments"])


@departments_router.post(
    path="/",
    response_model=DepartmentDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Add department",
)
async def add_department(
        request: DepartmentCreate,
        department_service: DepartmentService = Depends(get_department_service),
) -> DepartmentDTO:
    department = await department_service.add_department(
        name=request.name,
        parent_id=request.parent_id,
    )
    return DepartmentDTO.model_validate(department)


@departments_router.post(
    path="/{id}/employees/",
    response_model=AddEmployeeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add employee in department",
)
async def add_employee(
        request: AddEmployeeRequest,
        id: Annotated[int, Path(..., ge=1, description="Department ID")],
        employee_service: EmployeeService = Depends(get_employee_service),
) -> AddEmployeeResponse:
    employee = await employee_service.add_employee(
        department_id=id,
        full_name=request.full_name,
        position=request.position,
        hired_at=request.hired_at,
    )
    return AddEmployeeResponse(
        employee=EmployeeDTO.model_validate(employee),
    )


@departments_router.get(
    path="/{id}",
    response_model=DepartmentDetailsDTO,
    status_code=status.HTTP_200_OK,
    summary="Get department details",
)
async def get_department(
        id: Annotated[int, Path(..., ge=1, description="Department ID")],
        depth: Annotated[int, Query(ge=1, le=5, description="Depth of nested departments")] = 1,
        include_employees: Annotated[bool, Query(description="Include employees in response")] = True,
        department_service: DepartmentService = Depends(get_department_service),
) -> DepartmentDetailsDTO:
    return await department_service.get_department_details(
        department_id=id,
        depth=depth,
        include_employees=include_employees,
    )


@departments_router.patch(
    path="/{id}",
    response_model=DepartmentDTO,
    status_code=status.HTTP_200_OK,
    summary="Update department",
)
async def update_department(
        request: DepartmentUpdate,
        id: Annotated[int, Path(..., ge=1, description="Department ID")],
        department_service: DepartmentService = Depends(get_department_service),
) -> DepartmentDTO:
    department = await department_service.update_department(
        department_id=id,
        payload=request,
    )
    return DepartmentDTO.model_validate(department)

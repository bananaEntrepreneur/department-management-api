from fastapi import APIRouter, Depends
from starlette import status

from app.core.dependencies import get_department_service
from app.schemas.department import DepartmentCreate, DepartmentDTO
from app.services.department import DepartmentService

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

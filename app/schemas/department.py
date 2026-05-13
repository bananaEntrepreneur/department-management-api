from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.employee import EmployeeDTO
from app.schemas.text import NonEmptyText


class DepartmentDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., ge=1, description="ID of the department")
    name: str = Field(..., description="Name of the department")
    parent_id: int | None = Field(None, ge=1, description="ID of the parent department")
    created_at: datetime = Field(..., description="Date the department was created")


class DepartmentCreate(BaseModel):
    name: NonEmptyText = Field(..., description="Name of the department")
    parent_id: int | None = Field(None, ge=1, description="ID of the parent department")


class DepartmentUpdate(BaseModel):
    name: NonEmptyText | None = Field(None, description="Name of the department")
    parent_id: int | None = Field(None, ge=1, description="ID of the parent department")


class DepartmentDetailsDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    department: DepartmentDTO
    employees: list[EmployeeDTO] = Field(default_factory=list)
    children: list["DepartmentDetailsDTO"] = Field(default_factory=list)


DepartmentDetailsDTO.model_rebuild()

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.text import NonEmptyText


class EmployeeDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., ge=1, description="ID of the employee")
    department_id: int = Field(..., ge=1, description="ID of the department")
    full_name: NonEmptyText = Field(..., description="Full name of the employee")
    position: NonEmptyText = Field(..., description="Position of the employee")
    hired_at: date | None = Field(None, description="Hiring date")
    created_at: datetime = Field(..., description="Date the employee was created")


class AddEmployeeRequest(BaseModel):
    full_name: NonEmptyText = Field(..., description="Full name of the employee")
    position: NonEmptyText = Field(..., description="Position of the employee")
    hired_at: date | None = Field(None, description="Hiring date")

    @field_validator("hired_at")
    @classmethod
    def validate_hired_at(cls, value: date | None) -> date | None:
        if value is not None and value > date.today():
            raise ValueError("hired_at must not be in the future")
        return value


class AddEmployeeResponse(BaseModel):
    employee: EmployeeDTO

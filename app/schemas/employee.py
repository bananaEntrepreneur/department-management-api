from __future__ import annotations

from datetime import date, datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

FullNameText = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=200),
]

EmployeeText = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=2, max_length=255),
]


class EmployeeDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., ge=1, description="ID of the employee")
    department_id: int = Field(..., ge=1, description="ID of the department")
    full_name: FullNameText = Field(..., description="Full name of the employee")
    position: EmployeeText = Field(..., description="Position of the employee")
    hired_at: date | None = Field(None, description="Hiring date")
    created_at: datetime = Field(..., description="Date the employee was created")


class AddEmployeeRequest(BaseModel):
    full_name: FullNameText = Field(..., description="Full name of the employee")
    position: EmployeeText = Field(..., description="Position of the employee")
    hired_at: date | None = Field(None, description="Hiring date")

    @field_validator("hired_at")
    @classmethod
    def validate_hired_at(cls, value: date | None) -> date | None:
        if value is not None and value > date.today():
            raise ValueError("hired_at must not be in the future")
        return value


class AddEmployeeResponse(BaseModel):
    employee: EmployeeDTO

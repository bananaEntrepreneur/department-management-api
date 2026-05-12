from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class DepartmentDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., ge=1, description="ID of the department")
    name: str = Field(..., description="Name of the department")
    parent_id: int | None = Field(None, ge=1, description="ID of the parent department")
    created_at: datetime = Field(..., description="Date the department was created")


class DepartmentCreate(BaseModel):
    name: NonEmptyStr = Field(..., description="Name of the department")
    parent_id: int | None = Field(None, ge=1, description="ID of the parent department")

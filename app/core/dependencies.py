from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import db
from app.services.department import DepartmentService


async def get_department_service(
    db: AsyncSession = Depends(db.session_dependency),
) -> DepartmentService:
    return DepartmentService(db)

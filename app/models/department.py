from __future__ import annotations

from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from app.models.base import Base


class Department(Base):
    __tablename__ = "departments"
    __table_args__ = (
        CheckConstraint("trim(name) <> ''", name="ck_departments_name_not_blank"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    parent_id = Column(Integer, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    parent = relationship(
        "Department",
        remote_side=lambda: [Department.id],
        back_populates="children",
    )
    children = relationship(
        "Department",
        back_populates="parent",
    )
    employees = relationship("Employee", back_populates="department")

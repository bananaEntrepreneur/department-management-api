"""add cascade foreign keys

Revision ID: 20260513_03
Revises: 20260513_02
Create Date: 2026-05-13 00:00:00.000000
"""

from __future__ import annotations

from alembic import op


revision = "20260513_03"
down_revision = "20260513_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint(
        "fk_employees_department_id_departments",
        "employees",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "fk_employees_department_id_departments",
        "employees",
        "departments",
        ["department_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.drop_constraint(
        "fk_departments_parent_id_departments",
        "departments",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "fk_departments_parent_id_departments",
        "departments",
        "departments",
        ["parent_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_departments_parent_id_departments",
        "departments",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "fk_departments_parent_id_departments",
        "departments",
        "departments",
        ["parent_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.drop_constraint(
        "fk_employees_department_id_departments",
        "employees",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "fk_employees_department_id_departments",
        "employees",
        "departments",
        ["department_id"],
        ["id"],
    )

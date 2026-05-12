"""add employees table

Revision ID: 20260513_02
Revises: 20260513_01
Create Date: 2026-05-13 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260513_02"
down_revision = "20260513_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "employees",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("department_id", sa.Integer(), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("position", sa.String(length=255), nullable=False),
        sa.Column("hired_at", sa.Date(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("trim(full_name) <> ''", name="ck_employees_full_name_not_blank"),
        sa.CheckConstraint("trim(position) <> ''", name="ck_employees_position_not_blank"),
        sa.ForeignKeyConstraint(
            ["department_id"],
            ["departments.id"],
            name="fk_employees_department_id_departments",
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("employees")

"""add complaint sla policies

Revision ID: fa40d3f48c21
Revises: f2a6e8327c10
Create Date: 2026-04-30 00:00:00.000000

"""
from datetime import datetime
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "fa40d3f48c21"
down_revision: Union[str, None] = "f2a6e8327c10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "complaint_sla_policies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("severity", sa.String(length=50), nullable=False),
        sa.Column("response_hours", sa.Integer(), nullable=False),
        sa.Column("resolution_hours", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("severity"),
    )
    op.create_index(op.f("ix_complaint_sla_policies_id"), "complaint_sla_policies", ["id"], unique=False)
    op.create_index(op.f("ix_complaint_sla_policies_severity"), "complaint_sla_policies", ["severity"], unique=True)

    policies = sa.table(
        "complaint_sla_policies",
        sa.column("severity", sa.String),
        sa.column("response_hours", sa.Integer),
        sa.column("resolution_hours", sa.Integer),
        sa.column("created_at", sa.DateTime),
        sa.column("updated_at", sa.DateTime),
    )
    now = datetime.utcnow()
    op.bulk_insert(
        policies,
        [
            {"severity": "low", "response_hours": 24, "resolution_hours": 96, "created_at": now, "updated_at": now},
            {"severity": "medium", "response_hours": 12, "resolution_hours": 48, "created_at": now, "updated_at": now},
            {"severity": "high", "response_hours": 4, "resolution_hours": 24, "created_at": now, "updated_at": now},
            {"severity": "urgent", "response_hours": 1, "resolution_hours": 8, "created_at": now, "updated_at": now},
        ],
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_complaint_sla_policies_severity"), table_name="complaint_sla_policies")
    op.drop_index(op.f("ix_complaint_sla_policies_id"), table_name="complaint_sla_policies")
    op.drop_table("complaint_sla_policies")

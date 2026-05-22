"""add worker_interests table

Revision ID: g1h2i3j4k5l6
Revises: c4e15d7b9a20
Create Date: 2026-05-06 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "g1h2i3j4k5l6"
down_revision: Union[str, None] = "c4e15d7b9a20"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "worker_interests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("worker_profile_id", sa.Integer(), nullable=False),
        sa.Column("requirement_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("expressed_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["worker_profile_id"], ["worker_profiles.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["requirement_id"], ["requirements.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "worker_profile_id",
            "requirement_id",
            name="uq_worker_interest_requirement",
        ),
    )
    op.create_index(
        op.f("ix_worker_interests_id"), "worker_interests", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_worker_interests_worker_profile_id"),
        "worker_interests",
        ["worker_profile_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_worker_interests_requirement_id"),
        "worker_interests",
        ["requirement_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_worker_interests_status"),
        "worker_interests",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_worker_interests_status"), table_name="worker_interests")
    op.drop_index(
        op.f("ix_worker_interests_requirement_id"), table_name="worker_interests"
    )
    op.drop_index(
        op.f("ix_worker_interests_worker_profile_id"), table_name="worker_interests"
    )
    op.drop_index(op.f("ix_worker_interests_id"), table_name="worker_interests")
    op.drop_table("worker_interests")

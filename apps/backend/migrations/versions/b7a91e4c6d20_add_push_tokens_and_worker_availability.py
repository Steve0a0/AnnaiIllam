"""add push tokens and worker availability

Revision ID: b7a91e4c6d20
Revises: fa40d3f48c21
Create Date: 2026-04-30 03:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b7a91e4c6d20"
down_revision: Union[str, None] = "fa40d3f48c21"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "push_tokens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token", sa.String(length=512), nullable=False),
        sa.Column("platform", sa.String(length=50), nullable=False),
        sa.Column("app_variant", sa.String(length=50), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token", name="uq_push_tokens_token"),
    )
    op.create_index(op.f("ix_push_tokens_id"), "push_tokens", ["id"], unique=False)
    op.create_index(op.f("ix_push_tokens_is_active"), "push_tokens", ["is_active"], unique=False)
    op.create_index(op.f("ix_push_tokens_token"), "push_tokens", ["token"], unique=False)
    op.create_index(op.f("ix_push_tokens_user_id"), "push_tokens", ["user_id"], unique=False)

    op.create_table(
        "worker_availability",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("worker_profile_id", sa.Integer(), nullable=False),
        sa.Column("availability_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["worker_profile_id"], ["worker_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("worker_profile_id", "availability_date", name="uq_worker_availability_date"),
    )
    op.create_index(op.f("ix_worker_availability_availability_date"), "worker_availability", ["availability_date"], unique=False)
    op.create_index(op.f("ix_worker_availability_id"), "worker_availability", ["id"], unique=False)
    op.create_index(op.f("ix_worker_availability_status"), "worker_availability", ["status"], unique=False)
    op.create_index(op.f("ix_worker_availability_worker_profile_id"), "worker_availability", ["worker_profile_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_worker_availability_worker_profile_id"), table_name="worker_availability")
    op.drop_index(op.f("ix_worker_availability_status"), table_name="worker_availability")
    op.drop_index(op.f("ix_worker_availability_id"), table_name="worker_availability")
    op.drop_index(op.f("ix_worker_availability_availability_date"), table_name="worker_availability")
    op.drop_table("worker_availability")

    op.drop_index(op.f("ix_push_tokens_user_id"), table_name="push_tokens")
    op.drop_index(op.f("ix_push_tokens_token"), table_name="push_tokens")
    op.drop_index(op.f("ix_push_tokens_is_active"), table_name="push_tokens")
    op.drop_index(op.f("ix_push_tokens_id"), table_name="push_tokens")
    op.drop_table("push_tokens")

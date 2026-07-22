"""Add account deletion and data export requests.

Revision ID: f4b2c7d91a30
Revises: e8f91b24c6a0
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "f4b2c7d91a30"
down_revision: str | None = "e8f91b24c6a0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "privacy_requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("request_type", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.Column("requested_at", sa.DateTime(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("resolved_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("request_type IN ('deletion', 'export')", name="ck_privacy_requests_type"),
        sa.CheckConstraint("status IN ('pending', 'in_review', 'completed', 'rejected')", name="ck_privacy_requests_status"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["resolved_by_user_id"], ["users.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_privacy_requests_id", "privacy_requests", ["id"])
    op.create_index("ix_privacy_requests_user_id", "privacy_requests", ["user_id"])
    op.create_index("ix_privacy_requests_request_type", "privacy_requests", ["request_type"])
    op.create_index("ix_privacy_requests_status", "privacy_requests", ["status"])
    op.create_index("ix_privacy_requests_resolved_by_user_id", "privacy_requests", ["resolved_by_user_id"])
    op.create_index(
        "uq_privacy_requests_open_user_type",
        "privacy_requests",
        ["user_id", "request_type"],
        unique=True,
        postgresql_where=sa.text("status IN ('pending', 'in_review')"),
    )


def downgrade() -> None:
    op.drop_index("uq_privacy_requests_open_user_type", table_name="privacy_requests")
    op.drop_index("ix_privacy_requests_resolved_by_user_id", table_name="privacy_requests")
    op.drop_index("ix_privacy_requests_status", table_name="privacy_requests")
    op.drop_index("ix_privacy_requests_request_type", table_name="privacy_requests")
    op.drop_index("ix_privacy_requests_user_id", table_name="privacy_requests")
    op.drop_index("ix_privacy_requests_id", table_name="privacy_requests")
    op.drop_table("privacy_requests")

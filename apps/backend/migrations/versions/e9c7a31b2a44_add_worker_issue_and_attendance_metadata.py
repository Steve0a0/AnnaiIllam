"""add worker issue and attendance metadata

Revision ID: e9c7a31b2a44
Revises: d4f1d6c12b70
Create Date: 2026-04-29 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e9c7a31b2a44"
down_revision: Union[str, None] = "d4f1d6c12b70"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("attendance", sa.Column("check_in_latitude", sa.Float(), nullable=True))
    op.add_column("attendance", sa.Column("check_in_longitude", sa.Float(), nullable=True))
    op.add_column("attendance", sa.Column("check_out_latitude", sa.Float(), nullable=True))
    op.add_column("attendance", sa.Column("check_out_longitude", sa.Float(), nullable=True))
    op.add_column("attendance", sa.Column("check_in_selfie_url", sa.Text(), nullable=True))
    op.add_column("attendance", sa.Column("check_out_selfie_url", sa.Text(), nullable=True))
    op.add_column("attendance", sa.Column("qr_code", sa.String(length=255), nullable=True))
    op.create_index(op.f("ix_attendance_qr_code"), "attendance", ["qr_code"], unique=False)

    op.add_column("worker_documents", sa.Column("expiry_date", sa.Date(), nullable=True))
    op.create_index(op.f("ix_worker_documents_expiry_date"), "worker_documents", ["expiry_date"], unique=False)

    op.create_table(
        "worker_issues",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("worker_profile_id", sa.Integer(), nullable=False),
        sa.Column("assignment_id", sa.Integer(), nullable=True),
        sa.Column("issue_type", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["assignment_id"], ["assignments.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["worker_profile_id"], ["worker_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_worker_issues_assignment_id"), "worker_issues", ["assignment_id"], unique=False)
    op.create_index(op.f("ix_worker_issues_id"), "worker_issues", ["id"], unique=False)
    op.create_index(op.f("ix_worker_issues_issue_type"), "worker_issues", ["issue_type"], unique=False)
    op.create_index(op.f("ix_worker_issues_status"), "worker_issues", ["status"], unique=False)
    op.create_index(op.f("ix_worker_issues_worker_profile_id"), "worker_issues", ["worker_profile_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_worker_issues_worker_profile_id"), table_name="worker_issues")
    op.drop_index(op.f("ix_worker_issues_status"), table_name="worker_issues")
    op.drop_index(op.f("ix_worker_issues_issue_type"), table_name="worker_issues")
    op.drop_index(op.f("ix_worker_issues_id"), table_name="worker_issues")
    op.drop_index(op.f("ix_worker_issues_assignment_id"), table_name="worker_issues")
    op.drop_table("worker_issues")

    op.drop_index(op.f("ix_worker_documents_expiry_date"), table_name="worker_documents")
    op.drop_column("worker_documents", "expiry_date")

    op.drop_index(op.f("ix_attendance_qr_code"), table_name="attendance")
    op.drop_column("attendance", "qr_code")
    op.drop_column("attendance", "check_out_selfie_url")
    op.drop_column("attendance", "check_in_selfie_url")
    op.drop_column("attendance", "check_out_longitude")
    op.drop_column("attendance", "check_out_latitude")
    op.drop_column("attendance", "check_in_longitude")
    op.drop_column("attendance", "check_in_latitude")

"""Ensure one attendance row per assignment and business date.

Revision ID: b7e1c42d9a60
Revises: a4c8e91d2f30
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "b7e1c42d9a60"
down_revision: str | None = "a4c8e91d2f30"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

CONSTRAINT_NAME = "uq_attendance_assignment_date"
CONSTRAINT_COLUMNS = {"assignment_id", "attendance_date"}


def _unique_key_exists(bind) -> bool:
    inspector = sa.inspect(bind)
    return any(
        set(constraint.get("column_names") or []) == CONSTRAINT_COLUMNS
        for constraint in inspector.get_unique_constraints("attendance")
    )


def upgrade() -> None:
    bind = op.get_bind()
    if _unique_key_exists(bind):
        return

    # Repair schema drift safely before adding the invariant. Prefer a row with
    # a real check-in over an auto-generated no-show, then keep the newest row.
    op.execute(
        sa.text(
            """
            DELETE FROM attendance
            WHERE id IN (
                SELECT id
                FROM (
                    SELECT
                        id,
                        ROW_NUMBER() OVER (
                            PARTITION BY assignment_id, attendance_date
                            ORDER BY
                                CASE WHEN check_in_time IS NOT NULL THEN 0 ELSE 1 END,
                                id DESC
                        ) AS duplicate_rank
                    FROM attendance
                ) ranked_attendance
                WHERE duplicate_rank > 1
            )
            """
        )
    )

    if bind.dialect.name == "sqlite":
        with op.batch_alter_table("attendance") as batch_op:
            batch_op.create_unique_constraint(
                CONSTRAINT_NAME,
                ["assignment_id", "attendance_date"],
            )
    else:
        op.create_unique_constraint(
            CONSTRAINT_NAME,
            "attendance",
            ["assignment_id", "attendance_date"],
        )


def downgrade() -> None:
    # This invariant already exists in the original attendance-table migration.
    # A downgrade must not remove it from healthy databases or re-open payroll
    # corruption on a drifted database that this migration repaired.
    pass

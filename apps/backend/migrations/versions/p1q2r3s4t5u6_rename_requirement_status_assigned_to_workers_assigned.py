"""Rename requirement status 'assigned' to 'workers_assigned'.

Revision ID: p1q2r3s4t5u6
Revises: o1p2q3r4s5t6
Create Date: 2026-05-26

Updates every row in the requirements table where status = 'assigned'
to status = 'workers_assigned', aligning the database value with the
RequirementStatus.WORKERS_ASSIGNED enum and the frontend filter value.

AssignmentStatus 'assigned' (in the assignments table) is NOT touched.
"""

from alembic import op

revision = "p1q2r3s4t5u6"
down_revision = "o1p2q3r4s5t6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "UPDATE requirements SET status = 'workers_assigned' WHERE status = 'assigned'"
    )


def downgrade() -> None:
    op.execute(
        "UPDATE requirements SET status = 'assigned' WHERE status = 'workers_assigned'"
    )

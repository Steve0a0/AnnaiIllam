"""add replacement_reason and replaced_by_assignment_id to assignments

Revision ID: y1z2a3b4c5d6
Revises: x1y2z3a4b5c6
Create Date: 2026-05-28 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'y1z2a3b4c5d6'
down_revision = 'x1y2z3a4b5c6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('assignments', sa.Column('replacement_reason', sa.Text(), nullable=True))
    op.add_column(
        'assignments',
        sa.Column(
            'replaced_by_assignment_id',
            sa.Integer(),
            sa.ForeignKey('assignments.id', ondelete='SET NULL'),
            nullable=True,
        ),
    )
    op.create_index(
        op.f('ix_assignments_replaced_by_assignment_id'),
        'assignments',
        ['replaced_by_assignment_id'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_assignments_replaced_by_assignment_id'), table_name='assignments')
    op.drop_column('assignments', 'replaced_by_assignment_id')
    op.drop_column('assignments', 'replacement_reason')

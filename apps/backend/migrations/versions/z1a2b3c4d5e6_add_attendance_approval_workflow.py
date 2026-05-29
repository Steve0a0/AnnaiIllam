"""add attendance approval workflow columns

Revision ID: z1a2b3c4d5e6
Revises: y1z2a3b4c5d6
Create Date: 2026-05-28 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'z1a2b3c4d5e6'
down_revision = 'y1z2a3b4c5d6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('attendance', sa.Column('approval_status', sa.String(length=50), nullable=False, server_default='pending'))
    op.add_column(
        'attendance',
        sa.Column(
            'approved_by_user_id',
            sa.Integer(),
            sa.ForeignKey('users.id', ondelete='RESTRICT'),
            nullable=True,
        ),
    )
    op.add_column('attendance', sa.Column('approved_at', sa.DateTime(), nullable=True))
    op.add_column('attendance', sa.Column('approval_notes', sa.Text(), nullable=True))
    op.create_index(op.f('ix_attendance_approval_status'), 'attendance', ['approval_status'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_attendance_approval_status'), table_name='attendance')
    op.drop_column('attendance', 'approval_notes')
    op.drop_column('attendance', 'approved_at')
    op.drop_column('attendance', 'approved_by_user_id')
    op.drop_column('attendance', 'approval_status')

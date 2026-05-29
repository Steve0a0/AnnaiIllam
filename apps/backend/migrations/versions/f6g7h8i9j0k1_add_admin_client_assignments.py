"""add admin_client_assignments table

Revision ID: f6g7h8i9j0k1
Revises: e6f7g8h9i0j1
Create Date: 2026-05-29 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'f6g7h8i9j0k1'
down_revision = 'e6f7g8h9i0j1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'admin_client_assignments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('admin_user_id', sa.Integer(), nullable=False),
        sa.Column('client_profile_id', sa.Integer(), nullable=False),
        sa.Column('assigned_by_user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['admin_user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['assigned_by_user_id'], ['users.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['client_profile_id'], ['client_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('admin_user_id', 'client_profile_id', name='uq_admin_client_assignment'),
    )
    op.create_index(op.f('ix_admin_client_assignments_id'), 'admin_client_assignments', ['id'], unique=False)
    op.create_index(op.f('ix_admin_client_assignments_admin_user_id'), 'admin_client_assignments', ['admin_user_id'], unique=False)
    op.create_index(op.f('ix_admin_client_assignments_client_profile_id'), 'admin_client_assignments', ['client_profile_id'], unique=False)
    op.create_index(op.f('ix_admin_client_assignments_assigned_by_user_id'), 'admin_client_assignments', ['assigned_by_user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_admin_client_assignments_assigned_by_user_id'), table_name='admin_client_assignments')
    op.drop_index(op.f('ix_admin_client_assignments_client_profile_id'), table_name='admin_client_assignments')
    op.drop_index(op.f('ix_admin_client_assignments_admin_user_id'), table_name='admin_client_assignments')
    op.drop_index(op.f('ix_admin_client_assignments_id'), table_name='admin_client_assignments')
    op.drop_table('admin_client_assignments')

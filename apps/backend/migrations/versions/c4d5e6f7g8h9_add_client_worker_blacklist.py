"""add client_worker_blacklist table

Revision ID: c4d5e6f7g8h9
Revises: b3c4d5e6f7g8
Create Date: 2026-05-28 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'c4d5e6f7g8h9'
down_revision = 'b3c4d5e6f7g8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'client_worker_blacklist',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('client_profile_id', sa.Integer(), nullable=False),
        sa.Column('worker_profile_id', sa.Integer(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('blacklisted_by_user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['blacklisted_by_user_id'], ['users.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['client_profile_id'], ['client_profiles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['worker_profile_id'], ['worker_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('client_profile_id', 'worker_profile_id', name='uq_blacklist_client_worker'),
    )
    op.create_index(op.f('ix_client_worker_blacklist_id'), 'client_worker_blacklist', ['id'], unique=False)
    op.create_index(op.f('ix_client_worker_blacklist_client_profile_id'), 'client_worker_blacklist', ['client_profile_id'], unique=False)
    op.create_index(op.f('ix_client_worker_blacklist_worker_profile_id'), 'client_worker_blacklist', ['worker_profile_id'], unique=False)
    op.create_index(op.f('ix_client_worker_blacklist_blacklisted_by_user_id'), 'client_worker_blacklist', ['blacklisted_by_user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_client_worker_blacklist_blacklisted_by_user_id'), table_name='client_worker_blacklist')
    op.drop_index(op.f('ix_client_worker_blacklist_worker_profile_id'), table_name='client_worker_blacklist')
    op.drop_index(op.f('ix_client_worker_blacklist_client_profile_id'), table_name='client_worker_blacklist')
    op.drop_index(op.f('ix_client_worker_blacklist_id'), table_name='client_worker_blacklist')
    op.drop_table('client_worker_blacklist')

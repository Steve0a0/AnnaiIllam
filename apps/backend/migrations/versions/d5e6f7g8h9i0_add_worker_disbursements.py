"""add worker_disbursements table

Revision ID: d5e6f7g8h9i0
Revises: c4d5e6f7g8h9
Create Date: 2026-05-28 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'd5e6f7g8h9i0'
down_revision = 'c4d5e6f7g8h9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'worker_disbursements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('assignment_id', sa.Integer(), nullable=False),
        sa.Column('worker_profile_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('disbursement_status', sa.String(length=50), nullable=False),
        sa.Column('scheduled_date', sa.Date(), nullable=False),
        sa.Column('paid_at', sa.DateTime(), nullable=True),
        sa.Column('payment_reference', sa.String(length=255), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_by_user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['assignment_id'], ['assignments.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['worker_profile_id'], ['worker_profiles.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('assignment_id', name='uq_disbursement_assignment'),
    )
    op.create_index(op.f('ix_worker_disbursements_id'), 'worker_disbursements', ['id'], unique=False)
    op.create_index(op.f('ix_worker_disbursements_assignment_id'), 'worker_disbursements', ['assignment_id'], unique=False)
    op.create_index(op.f('ix_worker_disbursements_worker_profile_id'), 'worker_disbursements', ['worker_profile_id'], unique=False)
    op.create_index(op.f('ix_worker_disbursements_disbursement_status'), 'worker_disbursements', ['disbursement_status'], unique=False)
    op.create_index(op.f('ix_worker_disbursements_created_by_user_id'), 'worker_disbursements', ['created_by_user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_worker_disbursements_created_by_user_id'), table_name='worker_disbursements')
    op.drop_index(op.f('ix_worker_disbursements_disbursement_status'), table_name='worker_disbursements')
    op.drop_index(op.f('ix_worker_disbursements_worker_profile_id'), table_name='worker_disbursements')
    op.drop_index(op.f('ix_worker_disbursements_assignment_id'), table_name='worker_disbursements')
    op.drop_index(op.f('ix_worker_disbursements_id'), table_name='worker_disbursements')
    op.drop_table('worker_disbursements')

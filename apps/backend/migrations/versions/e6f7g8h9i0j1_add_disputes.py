"""add disputes and dispute_credit_notes tables

Revision ID: e6f7g8h9i0j1
Revises: d5e6f7g8h9i0
Create Date: 2026-05-29 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'e6f7g8h9i0j1'
down_revision = 'd5e6f7g8h9i0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'disputes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('requirement_id', sa.Integer(), nullable=False),
        sa.Column('raised_by_user_id', sa.Integer(), nullable=False),
        sa.Column('dispute_type', sa.String(50), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='open'),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('resolved_by_user_id', sa.Integer(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('credit_amount', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['raised_by_user_id'], ['users.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['requirement_id'], ['requirements.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['resolved_by_user_id'], ['users.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_disputes_id'), 'disputes', ['id'], unique=False)
    op.create_index(op.f('ix_disputes_requirement_id'), 'disputes', ['requirement_id'], unique=False)
    op.create_index(op.f('ix_disputes_raised_by_user_id'), 'disputes', ['raised_by_user_id'], unique=False)
    op.create_index(op.f('ix_disputes_dispute_type'), 'disputes', ['dispute_type'], unique=False)
    op.create_index(op.f('ix_disputes_status'), 'disputes', ['status'], unique=False)

    op.create_table(
        'dispute_credit_notes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('dispute_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('created_by_user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['dispute_id'], ['disputes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_dispute_credit_notes_id'), 'dispute_credit_notes', ['id'], unique=False)
    op.create_index(op.f('ix_dispute_credit_notes_dispute_id'), 'dispute_credit_notes', ['dispute_id'], unique=False)
    op.create_index(op.f('ix_dispute_credit_notes_created_by_user_id'), 'dispute_credit_notes', ['created_by_user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_dispute_credit_notes_created_by_user_id'), table_name='dispute_credit_notes')
    op.drop_index(op.f('ix_dispute_credit_notes_dispute_id'), table_name='dispute_credit_notes')
    op.drop_index(op.f('ix_dispute_credit_notes_id'), table_name='dispute_credit_notes')
    op.drop_table('dispute_credit_notes')

    op.drop_index(op.f('ix_disputes_status'), table_name='disputes')
    op.drop_index(op.f('ix_disputes_dispute_type'), table_name='disputes')
    op.drop_index(op.f('ix_disputes_raised_by_user_id'), table_name='disputes')
    op.drop_index(op.f('ix_disputes_requirement_id'), table_name='disputes')
    op.drop_index(op.f('ix_disputes_id'), table_name='disputes')
    op.drop_table('disputes')

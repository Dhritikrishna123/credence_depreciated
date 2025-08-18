"""add disputes

Revision ID: 0002_disputes
Revises: 0001_initial
Create Date: 2025-08-18 00:05:00

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0002_disputes'
down_revision = '0001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'disputes',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('ledger_entry_id', sa.Integer(), sa.ForeignKey('ledger_entries.id'), nullable=False),
        sa.Column('opened_by', sa.String(length=128), nullable=False),
        sa.Column('reason', sa.String(length=512), nullable=False),
        sa.Column('status', sa.Enum('open', 'resolved', 'rejected', name='dispute_status'), nullable=False, server_default='open'),
        sa.Column('resolution_note', sa.String(length=1024), nullable=True),
        sa.Column('resolved_by', sa.String(length=128), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('ix_disputes_status', 'disputes', ['status'])
    op.create_index('ix_disputes_created', 'disputes', ['created_at'])


def downgrade() -> None:
    op.drop_index('ix_disputes_created', table_name='disputes')
    op.drop_index('ix_disputes_status', table_name='disputes')
    op.drop_table('disputes')



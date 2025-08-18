"""initial schema

Revision ID: 0001_initial
Revises: 
Create Date: 2025-08-18 00:00:00

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'ledger_entries',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.String(length=128), nullable=False, index=True),
        sa.Column('domain', sa.String(length=64), nullable=False, index=True),
        sa.Column('action', sa.String(length=64), nullable=False),
        sa.Column('points', sa.Integer(), nullable=False),
        sa.Column('evidence_ref', sa.String(length=512), nullable=True),
        sa.Column('evidence_status', sa.Enum('green', 'yellow', 'red', name='evidence_status'), nullable=False, server_default='green'),
        sa.Column('related_entry_id', sa.Integer(), sa.ForeignKey('ledger_entries.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('ix_ledger_user', 'ledger_entries', ['user_id'])
    op.create_index('ix_ledger_domain', 'ledger_entries', ['domain'])
    op.create_index('ix_ledger_created_at', 'ledger_entries', ['created_at'])

    op.create_table(
        'verifications',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.String(length=128), nullable=False, index=True),
        sa.Column('source', sa.String(length=32), nullable=False),
        sa.Column('level', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('ix_verifications_user', 'verifications', ['user_id'])

    op.create_table(
        'idempotency_keys',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('key', sa.String(length=128), nullable=False, unique=True),
        sa.Column('user_id', sa.String(length=128), nullable=False),
        sa.Column('domain', sa.String(length=64), nullable=False),
        sa.Column('action', sa.String(length=64), nullable=False),
        sa.Column('ledger_entry_id', sa.Integer(), sa.ForeignKey('ledger_entries.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('ix_idem_key', 'idempotency_keys', ['key'], unique=True)
    op.create_index('ix_idem_user', 'idempotency_keys', ['user_id'])


def downgrade() -> None:
    op.drop_index('ix_idem_user', table_name='idempotency_keys')
    op.drop_index('ix_idem_key', table_name='idempotency_keys')
    op.drop_table('idempotency_keys')

    op.drop_index('ix_verifications_user', table_name='verifications')
    op.drop_table('verifications')

    op.drop_index('ix_ledger_created_at', table_name='ledger_entries')
    op.drop_index('ix_ledger_domain', table_name='ledger_entries')
    op.drop_index('ix_ledger_user', table_name='ledger_entries')
    op.drop_table('ledger_entries')



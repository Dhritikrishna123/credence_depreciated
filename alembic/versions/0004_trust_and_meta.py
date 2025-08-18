"""trust scores, evidence flags, ledger meta

Revision ID: 0004_trust_and_meta
Revises: 0003_append_only_ledger
Create Date: 2025-08-18 00:20:00

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0004_trust_and_meta'
down_revision = '0003_append_only_ledger'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add meta column to ledger_entries
    op.add_column('ledger_entries', sa.Column('meta', sa.JSON(), nullable=True))

    # trust_scores table
    op.create_table(
        'trust_scores',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.String(length=128), nullable=False, index=True),
        sa.Column('domain', sa.String(length=64), nullable=True),
        sa.Column('trust', sa.Float(), nullable=False),
        sa.Column('karma_balance', sa.Integer(), nullable=False),
        sa.Column('verification_level', sa.Integer(), nullable=False),
        sa.Column('computed_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('ix_trust_scores_user', 'trust_scores', ['user_id'])
    op.create_index('ix_trust_scores_domain', 'trust_scores', ['domain'])
    op.create_index('ix_trust_scores_computed', 'trust_scores', ['computed_at'])

    # evidence_flags table
    op.create_table(
        'evidence_flags',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('ledger_entry_id', sa.Integer(), sa.ForeignKey('ledger_entries.id'), nullable=False),
        sa.Column('status', sa.Enum('green', 'yellow', 'red', name='evidence_status'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('ix_evidence_flags_created', 'evidence_flags', ['created_at'])


def downgrade() -> None:
    op.drop_index('ix_evidence_flags_created', table_name='evidence_flags')
    op.drop_table('evidence_flags')

    op.drop_index('ix_trust_scores_computed', table_name='trust_scores')
    op.drop_index('ix_trust_scores_domain', table_name='trust_scores')
    op.drop_index('ix_trust_scores_user', table_name='trust_scores')
    op.drop_table('trust_scores')

    op.drop_column('ledger_entries', 'meta')



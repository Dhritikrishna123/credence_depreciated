"""append-only protection for ledger_entries

Revision ID: 0003_append_only_ledger
Revises: 0002_disputes
Create Date: 2025-08-18 00:10:00

"""
from __future__ import annotations

from alembic import op


# revision identifiers, used by Alembic.
revision = '0003_append_only_ledger'
down_revision = '0002_disputes'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE OR REPLACE FUNCTION prevent_ledger_update_delete() RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'ledger_entries is append-only';
            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql;

        DROP TRIGGER IF EXISTS trg_ledger_no_update ON ledger_entries;
        CREATE TRIGGER trg_ledger_no_update
        BEFORE UPDATE ON ledger_entries
        FOR EACH ROW EXECUTE FUNCTION prevent_ledger_update_delete();

        DROP TRIGGER IF EXISTS trg_ledger_no_delete ON ledger_entries;
        CREATE TRIGGER trg_ledger_no_delete
        BEFORE DELETE ON ledger_entries
        FOR EACH ROW EXECUTE FUNCTION prevent_ledger_update_delete();
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TRIGGER IF EXISTS trg_ledger_no_delete ON ledger_entries;
        DROP TRIGGER IF EXISTS trg_ledger_no_update ON ledger_entries;
        DROP FUNCTION IF EXISTS prevent_ledger_update_delete();
        """
    )



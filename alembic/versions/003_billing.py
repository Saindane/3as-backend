"""Feature 3 - settings table with default values

Revision ID: 003_billing
Revises: 002_users_properties
Create Date: 2025-06-28
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "003_billing"
down_revision: Union[str, None] = "002_users_properties"
branch_labels = None
depends_on    = None


def upgrade() -> None:
    # ── settings table ────────────────────────────────────
    op.create_table(
        "settings",
        sa.Column("key",   sa.String(100), nullable=False),
        sa.Column("value", sa.String(500), nullable=False),
        sa.PrimaryKeyConstraint("key"),
    )

    # ── Default settings ──────────────────────────────────
    op.execute("""
        INSERT INTO settings (key, value) VALUES
        ('penalty_daily_pct',   '0.05'),
        ('upi_id',              '3ascomplex@upi'),
        ('society_name',        '3As Complex — Sunrise Tower'),
        ('society_address',     'Pune, Maharashtra 411001'),
        ('maintenance_amount',  '2000'),
        ('due_day_of_month',    '10'),
        ('fcm_enabled',         'true'),
        ('sms_enabled',         'false')
        ON CONFLICT (key) DO NOTHING
    """)

    # ── Add index on bills for faster queries ─────────────
    op.create_index("ix_bills_month_year",  "bills", ["month", "year"])
    op.create_index("ix_bills_status",      "bills", ["status"])


def downgrade() -> None:
    op.drop_index("ix_bills_status",    table_name="bills")
    op.drop_index("ix_bills_month_year",table_name="bills")
    op.drop_table("settings")

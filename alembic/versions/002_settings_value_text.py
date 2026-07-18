"""settings value column TEXT for logo base64

Revision ID: 002_settings_value_text
Revises: 
Create Date: 2026-07-18
"""
from alembic import op

revision = '002_settings_value_text'
down_revision = '001_fresh'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE settings ALTER COLUMN value TYPE TEXT")


def downgrade() -> None:
    op.execute("ALTER TABLE settings ALTER COLUMN value TYPE VARCHAR(500)")

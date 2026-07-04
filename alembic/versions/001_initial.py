"""Initial migration - users, otp_records, audit_logs

Revision ID: 001_initial
Revises: 
Create Date: 2025-06-28
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # users
    op.create_table(
        "users",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("mobile", sa.String(15), nullable=False),
        sa.Column("email", sa.String(150), nullable=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column(
            "role",
            sa.Enum("RESIDENT", "MANAGEMENT", "ADMIN", name="userrole"),
            nullable=False,
            server_default="RESIDENT",
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("fcm_token", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("user_id"),
    )
    op.create_index("ix_users_user_id", "users", ["user_id"])
    op.create_index("ix_users_mobile", "users", ["mobile"], unique=True)

    # otp_records
    op.create_table(
        "otp_records",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("mobile", sa.String(15), nullable=False),
        sa.Column("otp_hash", sa.String(255), nullable=False),
        sa.Column("purpose", sa.String(30), nullable=False),
        sa.Column("is_used", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_otp_records_mobile", "otp_records", ["mobile"])

    # audit_logs
    op.create_table(
        "audit_logs",
        sa.Column("log_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("entity", sa.String(50), nullable=True),
        sa.Column("entity_id", sa.Integer(), nullable=True),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("log_id"),
    )

    # Seed: default admin user (password: demo1234)
    op.execute("""
        INSERT INTO users (name, mobile, email, password_hash, role, is_active)
        VALUES (
            'Super Admin',
            '9999999999',
            'admin@3ascomplex.in',
            '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj2NqIdTh2/.',
            'ADMIN',
            true
        )
    """)


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("otp_records")
    op.drop_index("ix_users_mobile", table_name="users")
    op.drop_index("ix_users_user_id", table_name="users")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS userrole")

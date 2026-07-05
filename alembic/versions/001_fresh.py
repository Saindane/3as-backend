"""Fresh migration - all tables with correct enum values

Revision ID: 001_fresh
Revises:
Create Date: 2025-07-05

NOTE: This is a clean single migration replacing the previous 3 migrations.
      Drop your database and recreate it before running this.

      psql -U postgres -c "DROP DATABASE as3_db;"
      psql -U postgres -c "CREATE DATABASE as3_db;"
      alembic upgrade head
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001_fresh"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# ── Password hash for 'demo1234' (bcrypt rounds=12) ───────────────
DEMO_HASH = "$2b$12$EVKYF15wY90sP/CzblpKxubht3q6Cfg0EIZ3nEUR6xCpjqsrXmXuO"


def upgrade() -> None:

    # ── ENUMS ─────────────────────────────────────────────────────
    # Use lowercase to match what PostgreSQL SQLAlchemy creates by default
    userrole = postgresql.ENUM(
        "resident", "management", "admin",
        name="userrole", create_type=True
    )
    propertytype = postgresql.ENUM(
        "residential", "commercial",
        name="propertytype", create_type=True
    )
    occupancytype = postgresql.ENUM(
        "owner", "tenant",
        name="occupancytype", create_type=True
    )
    billstatus = postgresql.ENUM(
        "pending", "paid", "overdue", "waived",
        name="billstatus", create_type=True
    )
    paymentmode = postgresql.ENUM(
        "upi", "neft", "rtgs", "cash", "cheque",
        name="paymentmode", create_type=True
    )
    paymentstatus = postgresql.ENUM(
        "pending", "verified", "rejected",
        name="paymentstatus", create_type=True
    )
    complaintcategory = postgresql.ENUM(
        "electrical", "plumbing", "civil", "security",
        "housekeeping", "common_area", "other",
        name="complaintcategory", create_type=True
    )
    complaintpriority = postgresql.ENUM(
        "low", "medium", "high",
        name="complaintpriority", create_type=True
    )
    complaintstatus = postgresql.ENUM(
        "new", "assigned", "in_progress", "resolved", "closed",
        name="complaintstatus", create_type=True
    )

    # Create all enum types
    bind = op.get_bind()
    userrole.create(bind, checkfirst=True)
    propertytype.create(bind, checkfirst=True)
    occupancytype.create(bind, checkfirst=True)
    billstatus.create(bind, checkfirst=True)
    paymentmode.create(bind, checkfirst=True)
    paymentstatus.create(bind, checkfirst=True)
    complaintcategory.create(bind, checkfirst=True)
    complaintpriority.create(bind, checkfirst=True)
    complaintstatus.create(bind, checkfirst=True)

    # ── USERS ─────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("user_id",       sa.Integer(),      nullable=False),
        sa.Column("name",          sa.String(100),    nullable=False),
        sa.Column("mobile",        sa.String(15),     nullable=False),
        sa.Column("email",         sa.String(150),    nullable=True),
        sa.Column("password_hash", sa.String(255),    nullable=False),
        sa.Column("role",          sa.Enum("resident", "management", "admin", name="userrole"),
                  nullable=False, server_default="resident"),
        sa.Column("is_active",     sa.Boolean(),      nullable=False, server_default="true"),
        sa.Column("fcm_token",     sa.String(255),    nullable=True),
        sa.Column("created_at",    sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at",    sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("user_id"),
    )
    op.create_index("ix_users_user_id", "users", ["user_id"])
    op.create_index("ix_users_mobile",  "users", ["mobile"], unique=True)

    # ── OTP RECORDS ───────────────────────────────────────────────
    op.create_table(
        "otp_records",
        sa.Column("id",         sa.Integer(),              nullable=False),
        sa.Column("mobile",     sa.String(15),             nullable=False),
        sa.Column("otp_hash",   sa.String(255),            nullable=False),
        sa.Column("purpose",    sa.String(30),             nullable=False),
        sa.Column("is_used",    sa.Boolean(),              nullable=False, server_default="false"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_otp_records_mobile", "otp_records", ["mobile"])

    # ── AUDIT LOGS ────────────────────────────────────────────────
    op.create_table(
        "audit_logs",
        sa.Column("log_id",     sa.Integer(),    nullable=False),
        sa.Column("user_id",    sa.Integer(),    nullable=True),
        sa.Column("action",     sa.String(100),  nullable=False),
        sa.Column("entity",     sa.String(50),   nullable=True),
        sa.Column("entity_id",  sa.Integer(),    nullable=True),
        sa.Column("detail",     sa.Text(),       nullable=True),
        sa.Column("ip_address", sa.String(45),   nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("log_id"),
    )

    # ── PROPERTIES ────────────────────────────────────────────────
    op.create_table(
        "properties",
        sa.Column("property_id", sa.Integer(),  nullable=False),
        sa.Column("unit_no",     sa.String(20), nullable=False),
        sa.Column("floor",       sa.Integer(),  nullable=False),
        sa.Column("type",        sa.Enum("residential", "commercial", name="propertytype"),
                  nullable=False, server_default="residential"),
        sa.Column("area_sqft",   sa.Float(),    nullable=True),
        sa.Column("owner_id",    sa.Integer(),  nullable=True),
        sa.Column("created_at",  sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at",  sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["owner_id"], ["users.user_id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("property_id"),
        sa.UniqueConstraint("unit_no"),
    )
    op.create_index("ix_properties_property_id", "properties", ["property_id"])

    # ── OCCUPANTS ─────────────────────────────────────────────────
    op.create_table(
        "occupants",
        sa.Column("occupant_id",    sa.Integer(), nullable=False),
        sa.Column("property_id",    sa.Integer(), nullable=False),
        sa.Column("user_id",        sa.Integer(), nullable=False),
        sa.Column("occupancy_type", sa.Enum("owner", "tenant", name="occupancytype"),
                  nullable=False, server_default="owner"),
        sa.Column("created_at",     sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["property_id"], ["properties.property_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"],     ["users.user_id"],          ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("occupant_id"),
    )

    # ── BILLS ─────────────────────────────────────────────────────
    op.create_table(
        "bills",
        sa.Column("bill_id",     sa.Integer(), nullable=False),
        sa.Column("property_id", sa.Integer(), nullable=True),
        sa.Column("month",       sa.Integer(), nullable=False),
        sa.Column("year",        sa.Integer(), nullable=False),
        sa.Column("maintenance", sa.Float(),   nullable=False, server_default="0"),
        sa.Column("penalty",     sa.Float(),   nullable=False, server_default="0"),
        sa.Column("total",       sa.Float(),   nullable=False, server_default="0"),
        sa.Column("due_date",    sa.Date(),    nullable=True),
        sa.Column("status",      sa.Enum("pending", "paid", "overdue", "waived", name="billstatus"),
                  nullable=False, server_default="pending"),
        sa.Column("created_at",  sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at",  sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["property_id"], ["properties.property_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("bill_id"),
    )
    op.create_index("ix_bills_property_id", "bills", ["property_id"])
    op.create_index("ix_bills_month_year",  "bills", ["month", "year"])
    op.create_index("ix_bills_status",      "bills", ["status"])

    # ── PAYMENTS ──────────────────────────────────────────────────
    op.create_table(
        "payments",
        sa.Column("payment_id",  sa.Integer(),    nullable=False),
        sa.Column("bill_id",     sa.Integer(),    nullable=True),
        sa.Column("amount",      sa.Float(),      nullable=False),
        sa.Column("utr",         sa.String(100),  nullable=True),
        sa.Column("screenshot",  sa.String(500),  nullable=True),
        sa.Column("mode",        sa.Enum("upi", "neft", "rtgs", "cash", "cheque", name="paymentmode"),
                  nullable=False, server_default="upi"),
        sa.Column("status",      sa.Enum("pending", "verified", "rejected", name="paymentstatus"),
                  nullable=False, server_default="pending"),
        sa.Column("verified_by", sa.Integer(),    nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at",  sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["bill_id"],     ["bills.bill_id"],   ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["verified_by"], ["users.user_id"],   ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("payment_id"),
    )

    # ── COMPLAINTS ────────────────────────────────────────────────
    op.create_table(
        "complaints",
        sa.Column("complaint_id", sa.Integer(),    nullable=False),
        sa.Column("property_id",  sa.Integer(),    nullable=True),
        sa.Column("raised_by",    sa.Integer(),    nullable=True),
        sa.Column("assigned_to",  sa.Integer(),    nullable=True),
        sa.Column("category",
                  sa.Enum("electrical", "plumbing", "civil", "security",
                          "housekeeping", "common_area", "other",
                          name="complaintcategory"),
                  nullable=False),
        sa.Column("priority",
                  sa.Enum("low", "medium", "high", name="complaintpriority"),
                  nullable=False, server_default="medium"),
        sa.Column("status",
                  sa.Enum("new", "assigned", "in_progress", "resolved", "closed",
                          name="complaintstatus"),
                  nullable=False, server_default="new"),
        sa.Column("title",       sa.String(200), nullable=False),
        sa.Column("description", sa.Text(),      nullable=True),
        sa.Column("resolution",  sa.Text(),      nullable=True),
        sa.Column("created_at",  sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at",  sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["property_id"], ["properties.property_id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["raised_by"],   ["users.user_id"],          ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["assigned_to"], ["users.user_id"],          ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("complaint_id"),
    )

    # ── NOTICES ───────────────────────────────────────────────────
    op.create_table(
        "notices",
        sa.Column("notice_id",  sa.Integer(),   nullable=False),
        sa.Column("title",      sa.String(200), nullable=False),
        sa.Column("body",       sa.Text(),      nullable=False),
        sa.Column("category",   sa.String(50),  nullable=True),
        sa.Column("priority",   sa.String(20),  nullable=False, server_default="normal"),
        sa.Column("created_by", sa.Integer(),   nullable=True),
        sa.Column("is_active",  sa.Boolean(),   nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["created_by"], ["users.user_id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("notice_id"),
    )

    # ── SETTINGS ──────────────────────────────────────────────────
    op.create_table(
        "settings",
        sa.Column("key",   sa.String(100), nullable=False),
        sa.Column("value", sa.String(500), nullable=False),
        sa.PrimaryKeyConstraint("key"),
    )

    # ── SEED: default settings ────────────────────────────────────
    op.execute("""
        INSERT INTO settings (key, value) VALUES
        ('penalty_daily_pct',  '0.05'),
        ('upi_id',             '3ascomplex@upi'),
        ('society_name',       '3As Complex — Sunrise Tower'),
        ('society_address',    'Pune, Maharashtra 411001'),
        ('maintenance_amount', '2000'),
        ('due_day_of_month',   '10'),
        ('fcm_enabled',        'true'),
        ('sms_enabled',        'false')
        ON CONFLICT (key) DO NOTHING
    """)

    # ── SEED: demo users (password: demo1234) ─────────────────────
    op.execute(f"""
        INSERT INTO users (name, mobile, email, password_hash, role, is_active) VALUES
        ('Rajesh Kumar', '9876543210', 'rajesh@test.com', '{DEMO_HASH}', 'resident',   true),
        ('Priya Menon',  '8765432109', 'priya@test.com',  '{DEMO_HASH}', 'management', true),
        ('Suresh Admin', '7654321098', 'suresh@test.com', '{DEMO_HASH}', 'admin',      true),
        ('Super Admin',  '9999999999', 'admin@3ascomplex.in', '{DEMO_HASH}', 'admin', true)
        ON CONFLICT (mobile) DO NOTHING
    """)

    # ── SEED: demo properties ─────────────────────────────────────
    op.execute("""
        INSERT INTO properties (unit_no, floor, type, area_sqft, owner_id)
        SELECT '4B', 4, 'residential', 1050, user_id
        FROM users WHERE mobile = '9876543210'
        ON CONFLICT (unit_no) DO NOTHING
    """)
    op.execute("""
        INSERT INTO properties (unit_no, floor, type, area_sqft, owner_id)
        SELECT '2A', 2, 'residential', 850, user_id
        FROM users WHERE mobile = '8765432109'
        ON CONFLICT (unit_no) DO NOTHING
    """)

    # ── SEED: demo occupants ──────────────────────────────────────
    op.execute("""
        INSERT INTO occupants (property_id, user_id, occupancy_type)
        SELECT p.property_id, u.user_id, 'owner'
        FROM properties p
        JOIN users u ON u.mobile = '9876543210'
        WHERE p.unit_no = '4B'
        ON CONFLICT DO NOTHING
    """)


def downgrade() -> None:
    op.drop_table("settings")
    op.drop_table("notices")
    op.drop_table("complaints")
    op.drop_table("payments")
    op.drop_table("bills")
    op.drop_table("occupants")
    op.drop_table("properties")
    op.drop_table("audit_logs")
    op.drop_table("otp_records")
    op.drop_table("users")

    bind = op.get_bind()
    for enum_name in [
        "userrole", "propertytype", "occupancytype",
        "billstatus", "paymentmode", "paymentstatus",
        "complaintcategory", "complaintpriority", "complaintstatus",
    ]:
        bind.execute(sa.text(f"DROP TYPE IF EXISTS {enum_name}"))

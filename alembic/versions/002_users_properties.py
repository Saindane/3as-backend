"""Feature 2 - properties, occupants, bills, payments, complaints, notices stubs

Revision ID: 002_users_properties
Revises: 001_initial
Create Date: 2025-06-28
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "002_users_properties"
down_revision: Union[str, None] = "001_initial"
branch_labels = None
depends_on    = None


def upgrade() -> None:
    # ── properties ────────────────────────────────────────
    op.create_table(
        "properties",
        sa.Column("property_id", sa.Integer(), nullable=False),
        sa.Column("unit_no",     sa.String(20),  nullable=False),
        sa.Column("floor",       sa.Integer(),   nullable=False),
        sa.Column("type",        sa.Enum("residential", "commercial", name="propertytype"),
                  nullable=False, server_default="residential"),
        sa.Column("area_sqft",   sa.Float(),     nullable=True),
        sa.Column("owner_id",    sa.Integer(),   nullable=True),
        sa.Column("created_at",  sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at",  sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["owner_id"], ["users.user_id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("property_id"),
        sa.UniqueConstraint("unit_no"),
    )
    op.create_index("ix_properties_property_id", "properties", ["property_id"])

    # ── occupants ─────────────────────────────────────────
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

    # ── bills (stub) ──────────────────────────────────────
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
        sa.Column("status",
                  sa.Enum("pending", "paid", "overdue", "waived", name="billstatus"),
                  nullable=False, server_default="pending"),
        sa.Column("created_at",  sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at",  sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["property_id"], ["properties.property_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("bill_id"),
    )
    op.create_index("ix_bills_property_id", "bills", ["property_id"])

    # ── payments (stub) ───────────────────────────────────
    op.create_table(
        "payments",
        sa.Column("payment_id",  sa.Integer(),     nullable=False),
        sa.Column("bill_id",     sa.Integer(),     nullable=True),
        sa.Column("amount",      sa.Float(),       nullable=False),
        sa.Column("utr",         sa.String(100),   nullable=True),
        sa.Column("screenshot",  sa.String(500),   nullable=True),
        sa.Column("mode",
                  sa.Enum("upi", "neft", "rtgs", "cash", "cheque", name="paymentmode"),
                  nullable=False, server_default="upi"),
        sa.Column("status",
                  sa.Enum("pending", "verified", "rejected", name="paymentstatus"),
                  nullable=False, server_default="pending"),
        sa.Column("verified_by", sa.Integer(),     nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at",  sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["bill_id"],     ["bills.bill_id"],   ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["verified_by"], ["users.user_id"],   ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("payment_id"),
    )

    # ── complaints (stub) ─────────────────────────────────
    op.create_table(
        "complaints",
        sa.Column("complaint_id", sa.Integer(),     nullable=False),
        sa.Column("property_id",  sa.Integer(),     nullable=True),
        sa.Column("raised_by",    sa.Integer(),     nullable=True),
        sa.Column("assigned_to",  sa.Integer(),     nullable=True),
        sa.Column("category",
                  sa.Enum("electrical","plumbing","civil","security",
                          "housekeeping","common_area","other",
                          name="complaintcategory"),
                  nullable=False),
        sa.Column("priority",
                  sa.Enum("low","medium","high", name="complaintpriority"),
                  nullable=False, server_default="medium"),
        sa.Column("status",
                  sa.Enum("new","assigned","in_progress","resolved","closed",
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

    # ── notices (stub) ────────────────────────────────────
    op.create_table(
        "notices",
        sa.Column("notice_id",  sa.Integer(),    nullable=False),
        sa.Column("title",      sa.String(200),  nullable=False),
        sa.Column("body",       sa.Text(),       nullable=False),
        sa.Column("category",   sa.String(50),   nullable=True),
        sa.Column("priority",   sa.String(20),   nullable=False, server_default="normal"),
        sa.Column("created_by", sa.Integer(),    nullable=True),
        sa.Column("is_active",  sa.Boolean(),    nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["created_by"], ["users.user_id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("notice_id"),
    )

    # ── Seed demo data ────────────────────────────────────
    # Seed demo users (password: demo1234)
    op.execute("""
        INSERT INTO users (name, mobile, email, password_hash, role, is_active) VALUES
        ('Rajesh Kumar',  '9876543210', 'rajesh@test.com',
         '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj2NqIdTh2/.', 'resident', true),
        ('Priya Menon',   '8765432109', 'priya@test.com',
         '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj2NqIdTh2/.', 'management', true),
        ('Suresh Admin',  '7654321098', 'suresh@test.com',
         '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj2NqIdTh2/.', 'admin', true)
        ON CONFLICT (mobile) DO NOTHING
    """)

    # Seed demo properties
    op.execute("""
        INSERT INTO properties (unit_no, floor, type, area_sqft, owner_id)
        SELECT '4B', 4, 'residential', 1050, user_id FROM users WHERE mobile='9876543210'
        ON CONFLICT (unit_no) DO NOTHING
    """)
    op.execute("""
        INSERT INTO properties (unit_no, floor, type, area_sqft, owner_id)
        SELECT '2A', 2, 'residential', 850, user_id FROM users WHERE mobile='8765432109'
        ON CONFLICT (unit_no) DO NOTHING
    """)

    # Seed occupants
    op.execute("""
        INSERT INTO occupants (property_id, user_id, occupancy_type)
        SELECT p.property_id, u.user_id, 'owner'
        FROM properties p JOIN users u ON u.mobile='9876543210' WHERE p.unit_no='4B'
        ON CONFLICT DO NOTHING
    """)


def downgrade() -> None:
    op.drop_table("notices")
    op.drop_table("complaints")
    op.drop_table("payments")
    op.drop_table("bills")
    op.drop_table("occupants")
    op.drop_table("properties")
    for t in ["propertytype","occupancytype","billstatus","paymentmode",
              "paymentstatus","complaintcategory","complaintpriority","complaintstatus"]:
        op.execute(f"DROP TYPE IF EXISTS {t}")

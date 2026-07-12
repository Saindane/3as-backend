"""Fresh migration - all tables, correct lowercase enums, full seed data

Revision ID: 001_fresh
Revises:
Create Date: 2025-07-11
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "001_fresh"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# bcrypt hash for 'demo1234'
DEMO_HASH = "$2b$12$EVKYF15wY90sP/CzblpKxubht3q6Cfg0EIZ3nEUR6xCpjqsrXmXuO"


def upgrade() -> None:
    conn = op.get_bind()

    # ── 1. Drop all tables ────────────────────────────────────────
    conn.execute(sa.text("DROP TABLE IF EXISTS settings    CASCADE"))
    conn.execute(sa.text("DROP TABLE IF EXISTS notices     CASCADE"))
    conn.execute(sa.text("DROP TABLE IF EXISTS complaints  CASCADE"))
    conn.execute(sa.text("DROP TABLE IF EXISTS payments    CASCADE"))
    conn.execute(sa.text("DROP TABLE IF EXISTS bills       CASCADE"))
    conn.execute(sa.text("DROP TABLE IF EXISTS occupants   CASCADE"))
    conn.execute(sa.text("DROP TABLE IF EXISTS properties  CASCADE"))
    conn.execute(sa.text("DROP TABLE IF EXISTS audit_logs  CASCADE"))
    conn.execute(sa.text("DROP TABLE IF EXISTS otp_records CASCADE"))
    conn.execute(sa.text("DROP TABLE IF EXISTS users       CASCADE"))

    # ── 2. Drop all custom enum types ────────────────────────────
    conn.execute(sa.text("DROP TYPE IF EXISTS userrole          CASCADE"))
    conn.execute(sa.text("DROP TYPE IF EXISTS propertytype      CASCADE"))
    conn.execute(sa.text("DROP TYPE IF EXISTS occupancytype     CASCADE"))
    conn.execute(sa.text("DROP TYPE IF EXISTS billstatus        CASCADE"))
    conn.execute(sa.text("DROP TYPE IF EXISTS paymentmode       CASCADE"))
    conn.execute(sa.text("DROP TYPE IF EXISTS paymentstatus     CASCADE"))
    conn.execute(sa.text("DROP TYPE IF EXISTS complaintcategory CASCADE"))
    conn.execute(sa.text("DROP TYPE IF EXISTS complaintpriority CASCADE"))
    conn.execute(sa.text("DROP TYPE IF EXISTS complaintstatus   CASCADE"))

    # ── 3. Create enum types (ALL LOWERCASE) ─────────────────────
    conn.execute(sa.text("""
        CREATE TYPE userrole AS ENUM (
            'RESIDENT', 'MANAGEMENT', 'ADMIN'
        )
    """))
    conn.execute(sa.text("""
        CREATE TYPE propertytype AS ENUM (
            'RESIDENTIAL', 'COMMERCIAL'
        )
    """))
    conn.execute(sa.text("""
        CREATE TYPE occupancytype AS ENUM (
            'OWNER', 'TENANT'
        )
    """))
    conn.execute(sa.text("""
        CREATE TYPE billstatus AS ENUM (
            'PENDING', 'PAID', 'OVERDUE', 'WAIVED'
        )
    """))
    conn.execute(sa.text("""
        CREATE TYPE paymentmode AS ENUM (
            'UPI', 'NEFT', 'RTGS', 'CASH', 'CHEQUE'
        )
    """))
    conn.execute(sa.text("""
        CREATE TYPE paymentstatus AS ENUM (
            'PENDING', 'VERIFIED', 'REJECTED'
        )
    """))
    conn.execute(sa.text("""
        CREATE TYPE complaintcategory AS ENUM (
            'ELECTRICAL', 'PLUMBING', 'CIVIL', 'SECURITY',
            'HOUSEKEEPING', 'COMMON_AREA', 'OTHER'
        )
    """))
    conn.execute(sa.text("""
        CREATE TYPE complaintpriority AS ENUM (
            'LOW', 'MEDIUM', 'HIGH'
        )
    """))
    conn.execute(sa.text("""
        CREATE TYPE complaintstatus AS ENUM (
            'NEW', 'ASSIGNED', 'IN_PROGRESS', 'RESOLVED', 'CLOSED'
        )
    """))

    # ── 4. Create tables ──────────────────────────────────────────
    conn.execute(sa.text("""
        CREATE TABLE users (
            user_id       SERIAL PRIMARY KEY,
            name          VARCHAR(100)    NOT NULL,
            mobile        VARCHAR(15)     NOT NULL UNIQUE,
            email         VARCHAR(150),
            password_hash VARCHAR(255)    NOT NULL,
            role          userrole        NOT NULL DEFAULT 'RESIDENT',
            is_active     BOOLEAN         NOT NULL DEFAULT TRUE,
            fcm_token     VARCHAR(255),
            created_at    TIMESTAMPTZ     DEFAULT NOW(),
            updated_at    TIMESTAMPTZ     DEFAULT NOW()
        )
    """))
    conn.execute(sa.text("CREATE INDEX ix_users_user_id ON users(user_id)"))
    conn.execute(sa.text("CREATE UNIQUE INDEX ix_users_mobile ON users(mobile)"))

    conn.execute(sa.text("""
        CREATE TABLE otp_records (
            id         SERIAL PRIMARY KEY,
            mobile     VARCHAR(15)  NOT NULL,
            otp_hash   VARCHAR(255) NOT NULL,
            purpose    VARCHAR(30)  NOT NULL,
            is_used    BOOLEAN      NOT NULL DEFAULT FALSE,
            expires_at TIMESTAMPTZ  NOT NULL,
            created_at TIMESTAMPTZ  DEFAULT NOW()
        )
    """))
    conn.execute(sa.text("CREATE INDEX ix_otp_records_mobile ON otp_records(mobile)"))

    conn.execute(sa.text("""
        CREATE TABLE audit_logs (
            log_id     SERIAL PRIMARY KEY,
            user_id    INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
            action     VARCHAR(100) NOT NULL,
            entity     VARCHAR(50),
            entity_id  INTEGER,
            detail     TEXT,
            ip_address VARCHAR(45),
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """))

    conn.execute(sa.text("""
        CREATE TABLE properties (
            property_id SERIAL PRIMARY KEY,
            unit_no     VARCHAR(20)  NOT NULL UNIQUE,
            floor       INTEGER      NOT NULL,
            type        propertytype NOT NULL DEFAULT 'RESIDENTIAL',
            area_sqft   FLOAT,
            owner_id    INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
            created_at  TIMESTAMPTZ  DEFAULT NOW(),
            updated_at  TIMESTAMPTZ  DEFAULT NOW()
        )
    """))
    conn.execute(sa.text("CREATE INDEX ix_properties_property_id ON properties(property_id)"))

    conn.execute(sa.text("""
        CREATE TABLE occupants (
            occupant_id    SERIAL PRIMARY KEY,
            property_id    INTEGER       NOT NULL REFERENCES properties(property_id) ON DELETE CASCADE,
            user_id        INTEGER       NOT NULL REFERENCES users(user_id)          ON DELETE CASCADE,
            occupancy_type occupancytype NOT NULL DEFAULT 'OWNER',
            created_at     TIMESTAMPTZ   DEFAULT NOW()
        )
    """))

    conn.execute(sa.text("""
        CREATE TABLE bills (
            bill_id     SERIAL PRIMARY KEY,
            property_id INTEGER    REFERENCES properties(property_id) ON DELETE CASCADE,
            month       INTEGER    NOT NULL,
            year        INTEGER    NOT NULL,
            maintenance FLOAT      NOT NULL DEFAULT 0,
            penalty     FLOAT      NOT NULL DEFAULT 0,
            total       FLOAT      NOT NULL DEFAULT 0,
            due_date    DATE,
            status      billstatus NOT NULL DEFAULT 'PENDING',
            created_at  TIMESTAMPTZ DEFAULT NOW(),
            updated_at  TIMESTAMPTZ DEFAULT NOW()
        )
    """))
    conn.execute(sa.text("CREATE INDEX ix_bills_property_id ON bills(property_id)"))
    conn.execute(sa.text("CREATE INDEX ix_bills_month_year  ON bills(month, year)"))
    conn.execute(sa.text("CREATE INDEX ix_bills_status      ON bills(status)"))

    conn.execute(sa.text("""
        CREATE TABLE payments (
            payment_id  SERIAL PRIMARY KEY,
            bill_id     INTEGER       REFERENCES bills(bill_id)  ON DELETE CASCADE,
            amount      FLOAT         NOT NULL,
            utr         VARCHAR(100),
            screenshot  VARCHAR(500),
            mode        paymentmode   NOT NULL DEFAULT 'UPI',
            status      paymentstatus NOT NULL DEFAULT 'PENDING',
            verified_by INTEGER       REFERENCES users(user_id)  ON DELETE SET NULL,
            verified_at TIMESTAMPTZ,
            created_at  TIMESTAMPTZ   DEFAULT NOW()
        )
    """))

    conn.execute(sa.text("""
        CREATE TABLE complaints (
            complaint_id SERIAL PRIMARY KEY,
            property_id  INTEGER           REFERENCES properties(property_id) ON DELETE SET NULL,
            raised_by    INTEGER           REFERENCES users(user_id)          ON DELETE SET NULL,
            assigned_to  INTEGER           REFERENCES users(user_id)          ON DELETE SET NULL,
            category     complaintcategory NOT NULL,
            priority     complaintpriority NOT NULL DEFAULT 'MEDIUM',
            status       complaintstatus   NOT NULL DEFAULT 'NEW',
            title        VARCHAR(200)      NOT NULL,
            description  TEXT,
            resolution   TEXT,
            created_at   TIMESTAMPTZ DEFAULT NOW(),
            updated_at   TIMESTAMPTZ DEFAULT NOW()
        )
    """))

    conn.execute(sa.text("""
        CREATE TABLE notices (
            notice_id  SERIAL PRIMARY KEY,
            title      VARCHAR(200) NOT NULL,
            body       TEXT         NOT NULL,
            category   VARCHAR(50),
            priority   VARCHAR(20)  NOT NULL DEFAULT 'normal',
            created_by INTEGER      REFERENCES users(user_id) ON DELETE SET NULL,
            is_active  BOOLEAN      NOT NULL DEFAULT TRUE,
            created_at TIMESTAMPTZ  DEFAULT NOW(),
            updated_at TIMESTAMPTZ  DEFAULT NOW()
        )
    """))

    conn.execute(sa.text("""
        CREATE TABLE settings (
            key   VARCHAR(100) PRIMARY KEY,
            value VARCHAR(500) NOT NULL
        )
    """))

    # ── 5. Seed default settings ──────────────────────────────────
    conn.execute(sa.text("""
        INSERT INTO settings (key, value) VALUES
        ('penalty_daily_pct',  '0.05'),
        ('upi_id',             '3ascomplex@upi'),
        ('society_name',       '3As Complex Sunrise Tower'),
        ('society_address',    'Pune, Maharashtra 411001'),
        ('maintenance_amount', '2000'),
        ('due_day_of_month',   '10'),
        ('fcm_enabled',        'true'),
        ('sms_enabled',        'false'),
        ('app_name',            '3As Complex'),
        ('app_tagline',         'Maintenance Management System'),
        ('app_logo_url',        ''),
        ('app_primary_color',   '#2563EB')
    """))

    # ── 6. Seed demo users (password: demo1234) ───────────────────
    conn.execute(sa.text(f"""
        INSERT INTO users (name, mobile, email, password_hash, role, is_active)
        VALUES
        ('Rajesh Kumar', '9876543210', 'rajesh@test.com',
         '{DEMO_HASH}', 'RESIDENT', TRUE),
        ('Priya Menon',  '8765432109', 'priya@test.com',
         '{DEMO_HASH}', 'MANAGEMENT', TRUE),
        ('Suresh Admin', '7654321098', 'suresh@test.com',
         '{DEMO_HASH}', 'ADMIN', TRUE)
    """))

    # ── 7. Seed demo properties ───────────────────────────────────
    conn.execute(sa.text("""
        INSERT INTO properties (unit_no, floor, type, area_sqft, owner_id)
        SELECT '4B', 4, 'RESIDENTIAL', 1050, user_id
        FROM users WHERE mobile = '9876543210'
    """))
    conn.execute(sa.text("""
        INSERT INTO properties (unit_no, floor, type, area_sqft, owner_id)
        SELECT '2A', 2, 'RESIDENTIAL', 850, user_id
        FROM users WHERE mobile = '8765432109'
    """))

    # ── 8. Seed occupant ──────────────────────────────────────────
    conn.execute(sa.text("""
        INSERT INTO occupants (property_id, user_id, occupancy_type)
        SELECT p.property_id, u.user_id, 'OWNER'
        FROM properties p, users u
        WHERE p.unit_no = '4B' AND u.mobile = '9876543210'
    """))


def downgrade() -> None:
    conn = op.get_bind()
    for tbl in ["settings", "notices", "complaints", "payments",
                "bills", "occupants", "properties",
                "audit_logs", "otp_records", "users"]:
        conn.execute(sa.text(f"DROP TABLE IF EXISTS {tbl} CASCADE"))
    for enum in ["userrole", "propertytype", "occupancytype",
                 "billstatus", "paymentmode", "paymentstatus",
                 "complaintcategory", "complaintpriority", "complaintstatus"]:
        conn.execute(sa.text(f"DROP TYPE IF EXISTS {enum} CASCADE"))

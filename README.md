# 3As Complex — Backend API

FastAPI + PostgreSQL backend for the 3As Complex Maintenance Management System.

## Tech Stack
- **Framework**: FastAPI 0.110+
- **Database**: PostgreSQL 16 + SQLAlchemy 2.0 + Alembic
- **Auth**: JWT (python-jose) + bcrypt + OTP
- **Scheduler**: APScheduler (nightly penalty cron at 00:05 IST)

## Quick Start (Local — no Docker)

```bash
git clone https://github.com/Saindane/3as-backend.git
cd 3as-backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Create database in pgAdmin or psql:**
```sql
CREATE DATABASE as3_db;
```

**Configure .env:**
```bash
cp .env.example .env
# Edit .env — paste your SECRET_KEY (run: python -c "import secrets; print(secrets.token_hex(32))")
```

**Run migrations + start server:**
```bash
alembic upgrade head
uvicorn app.main:app --reload
```

API docs → http://localhost:8000/docs

## Database credentials
```
Host: localhost  |  Port: 5432  |  User: postgres  |  Password: Admin  |  Database: as3_db
```

## Demo accounts (seeded automatically)
| Name | Mobile | Password | Role |
|---|---|---|---|
| Rajesh Kumar | 9876543210 | demo1234 | resident |
| Priya Menon  | 8765432109 | demo1234 | management |
| Suresh Admin | 7654321098 | demo1234 | admin |

## Feature Implementation Status
- [x] **Feature 1** — Authentication: login, JWT, OTP, password reset
- [x] **Feature 2** — Users & Properties: CRUD, role guards, dashboard stats
- [x] **Feature 3** — Bills + Penalty Engine: bulk generation, nightly cron
- [x] **Feature 4** — Payments: submit UTR, screenshot, verify/reject
- [x] **Feature 5** — Complaints: raise, assign, track, resolve
- [x] **Feature 6** — Notices: publish, list, FCM push placeholder
- [x] **Feature 7** — MIS Reports: collection, defaulters, analytics, audit logs
- [x] **Feature 8** — Settings: configurable penalty rate, UPI, society info

## All API Endpoints
```
# Auth
POST   /api/v1/auth/login
POST   /api/v1/auth/refresh
GET    /api/v1/auth/me
POST   /api/v1/auth/otp/send
POST   /api/v1/auth/otp/verify
POST   /api/v1/auth/password/reset
POST   /api/v1/auth/fcm-token

# Users
GET    /api/v1/users
POST   /api/v1/users
GET    /api/v1/users/me
GET    /api/v1/users/:id
PATCH  /api/v1/users/:id
DELETE /api/v1/users/:id

# Properties
GET    /api/v1/properties
POST   /api/v1/properties
GET    /api/v1/properties/my
GET    /api/v1/properties/dashboard
GET    /api/v1/properties/:id
PATCH  /api/v1/properties/:id
DELETE /api/v1/properties/:id
POST   /api/v1/properties/:id/occupants

# Bills
GET    /api/v1/bills
POST   /api/v1/bills/generate
GET    /api/v1/bills/penalties/preview
POST   /api/v1/bills/penalties/apply
GET    /api/v1/bills/summary
GET    /api/v1/bills/:id
PATCH  /api/v1/bills/:id/waive

# Payments
GET    /api/v1/payments
GET    /api/v1/payments/pending
POST   /api/v1/payments
PATCH  /api/v1/payments/:id/verify

# Complaints
GET    /api/v1/complaints
POST   /api/v1/complaints
GET    /api/v1/complaints/:id
PATCH  /api/v1/complaints/:id
DELETE /api/v1/complaints/:id

# Notices
GET    /api/v1/notices
POST   /api/v1/notices
GET    /api/v1/notices/:id
PATCH  /api/v1/notices/:id
DELETE /api/v1/notices/:id

# Reports
GET    /api/v1/reports/collection
GET    /api/v1/reports/defaulters
GET    /api/v1/reports/complaints
GET    /api/v1/reports/audit-logs

# Settings
GET    /api/v1/settings
GET    /api/v1/settings/:key
PATCH  /api/v1/settings/:key
DELETE /api/v1/settings/:key
```

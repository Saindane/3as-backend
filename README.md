# 3As Complex — Backend API

FastAPI + PostgreSQL backend for the 3As Complex Maintenance Management System.

## Tech Stack
- **Framework**: FastAPI 0.110+
- **Database**: PostgreSQL 16 + SQLAlchemy 2.0 + Alembic
- **Auth**: JWT (python-jose) + bcrypt + OTP
- **Scheduler**: APScheduler (nightly penalty cron at 00:05 IST)
- **Storage**: AWS S3 / MinIO (payment screenshots)
- **Push**: Firebase Admin SDK (FCM)

## Project Structure
```
app/
├── api/v1/endpoints/   # Route handlers per module
├── core/               # Config, security, dependencies, scheduler
├── db/                 # Database session, base
├── models/             # SQLAlchemy ORM models
├── schemas/            # Pydantic request/response schemas
├── services/           # Business logic layer
└── utils/              # Helpers (OTP, FCM, S3)
tests/                  # pytest test suite
alembic/versions/       # DB migrations (001 → 003)
```

## Quick Start (Local — no Docker)

```bash
# 1. Clone and enter project
git clone https://github.com/Saindane/3as-backend.git
cd 3as-backend

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create database (PostgreSQL must be running)
createdb as3_db                 # password: Admin

# 5. Copy and configure .env
cp .env.example .env
# Edit .env — paste your SECRET_KEY (run: openssl rand -hex 32)

# 6. Run migrations (creates tables + seeds demo users)
alembic upgrade head

# 7. Start server
uvicorn app.main:app --reload
```

API docs → http://localhost:8000/docs

## Database credentials (local)
```
Host:     localhost
Port:     5432
User:     postgres
Password: Admin
Database: as3_db
```

## Demo accounts (seeded by migration)
| Name | Mobile | Password | Role |
|---|---|---|---|
| Rajesh Kumar | 9876543210 | demo1234 | Resident |
| Priya Menon  | 8765432109 | demo1234 | Management |
| Suresh Admin | 7654321098 | demo1234 | Admin |

## Feature Implementation Status
- [x] **Feature 1** — Authentication: login, JWT access+refresh tokens, OTP send/verify, password reset, FCM token, audit logs
- [x] **Feature 2** — Users & Properties: full CRUD, role-based guards (admin/mgmt/resident), occupant linking, dashboard stats
- [x] **Feature 3** — Bills + Penalty Engine: bulk generation, penalty formula (Outstanding × Daily% × Days), nightly APScheduler cron, collection summary, waive bill
- [ ] **Feature 4** — Payments: QR display, UTR + screenshot upload, payment verification by management
- [ ] **Feature 5** — Complaints: raise, assign, status tracking, resolution
- [ ] **Feature 6** — Notices + FCM Push: publish notices, broadcast push to all devices
- [ ] **Feature 7** — MIS Reports: collection report, defaulter list, complaint analytics, audit export
- [ ] **Feature 8** — Settings: penalty rate config, UPI/gateway config, society info

## Implemented API Endpoints
```
POST   /api/v1/auth/login
POST   /api/v1/auth/refresh
GET    /api/v1/auth/me
POST   /api/v1/auth/otp/send
POST   /api/v1/auth/otp/verify
POST   /api/v1/auth/password/reset
POST   /api/v1/auth/fcm-token

GET    /api/v1/users
POST   /api/v1/users
GET    /api/v1/users/me
GET    /api/v1/users/:id
PATCH  /api/v1/users/:id
DELETE /api/v1/users/:id

GET    /api/v1/properties
POST   /api/v1/properties
GET    /api/v1/properties/my
GET    /api/v1/properties/dashboard
GET    /api/v1/properties/:id
PATCH  /api/v1/properties/:id
DELETE /api/v1/properties/:id
POST   /api/v1/properties/:id/occupants

GET    /api/v1/bills
POST   /api/v1/bills/generate
GET    /api/v1/bills/penalties/preview
POST   /api/v1/bills/penalties/apply
GET    /api/v1/bills/summary
GET    /api/v1/bills/:id
PATCH  /api/v1/bills/:id/waive
```

## API Base URL
`/api/v1/`

All endpoints except `/auth/login`, `/auth/refresh`, `/auth/otp/*`, `/auth/password/reset` require:
```
Authorization: Bearer <access_token>
```

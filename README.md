# 3As Complex — Backend API

FastAPI + PostgreSQL backend for the 3As Complex Maintenance Management System.

## Tech Stack
- **Framework**: FastAPI 0.110+
- **Database**: PostgreSQL 16 + SQLAlchemy 2.0 + Alembic
- **Auth**: JWT (python-jose) + bcrypt + OTP
- **Scheduler**: APScheduler (nightly penalty cron)
- **Storage**: AWS S3 / MinIO (payment screenshots)
- **Push**: Firebase Admin SDK (FCM)
- **Containerisation**: Docker + Docker Compose

## Project Structure
```
app/
├── api/v1/endpoints/   # Route handlers per module
├── core/               # Config, security, dependencies
├── db/                 # Database session, base
├── models/             # SQLAlchemy ORM models
├── schemas/            # Pydantic request/response schemas
├── services/           # Business logic layer
└── utils/              # Helpers (OTP, FCM, S3)
tests/                  # pytest test suite
alembic/                # DB migrations
```

## Quick Start

```bash
# 1. Copy env file and fill in values
cp .env.example .env

# 2. Start with Docker
docker-compose up --build

# 3. Run migrations
docker-compose exec api alembic upgrade head

# 4. API docs available at
http://localhost:8000/docs
```

## Feature Implementation Status
- [x] **Feature 1**: Authentication (login, JWT, OTP, refresh, password reset)
- [ ] Feature 2: User & Property Management
- [ ] Feature 3: Bill Generation + Penalty Engine
- [ ] Feature 4: Payments
- [ ] Feature 5: Complaints
- [ ] Feature 6: Notices + FCM Push
- [ ] Feature 7: MIS Reports
- [ ] Feature 8: Settings + Admin

## API Base URL
`/api/v1/`

All endpoints (except `/auth`) require `Authorization: Bearer <access_token>` header.

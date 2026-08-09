from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1.router import api_router

import app.models  # noqa: F401 — registers all SQLAlchemy mappers

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="3As Complex Maintenance Management System — REST API",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────
# allow_credentials MUST be False when allow_origins=["*"]
# Tokens are sent via Authorization header (not cookies) so this is fine
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────
app.include_router(api_router)


# ── Scheduler ─────────────────────────────────────────────────────
@app.on_event("startup")
async def on_startup():
    import os, logging
    from alembic.config import Config
    from alembic import command

    logger = logging.getLogger("uvicorn")
    db_url = os.environ.get("DATABASE_URL", "")

    if not db_url:
        logger.error("DATABASE_URL not set — skipping migrations!")
        return

    # Fix Railway postgres:// → postgresql://
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    logger.info(f"Running alembic migrations...")
    try:
        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", db_url)
        command.upgrade(alembic_cfg, "head")
        logger.info("Migrations completed successfully!")
    except Exception as e:
        logger.error(f"Migration error: {e}")


@app.on_event("shutdown")
async def on_shutdown():
    pass


# ── Health ────────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "app": settings.APP_NAME}


@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}

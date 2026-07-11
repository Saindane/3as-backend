from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1.router import api_router
from app.core.scheduler import start_scheduler, stop_scheduler

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
    start_scheduler()


@app.on_event("shutdown")
async def on_shutdown():
    stop_scheduler()


# ── Health ────────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "app": settings.APP_NAME}


@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}

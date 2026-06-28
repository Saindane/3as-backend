from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1.router import api_router

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="3As Complex Maintenance Management System — REST API",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(api_router)


@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "app": settings.APP_NAME, "version": "1.0.0"}


@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}

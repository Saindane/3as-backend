from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth, users, properties, bills,
    payments, complaints, notices, reports, settings,
)

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(properties.router)
api_router.include_router(bills.router)
api_router.include_router(payments.router)
api_router.include_router(complaints.router)
api_router.include_router(notices.router)
api_router.include_router(reports.router)
api_router.include_router(settings.router)

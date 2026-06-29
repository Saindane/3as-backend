from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, properties, bills

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(properties.router)
api_router.include_router(bills.router)

# Coming next:
# from app.api.v1.endpoints import payments, complaints, notices, reports, settings

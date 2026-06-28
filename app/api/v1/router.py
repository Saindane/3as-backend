from fastapi import APIRouter
from app.api.v1.endpoints import auth

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)

# Future features will be added here:
# from app.api.v1.endpoints import users, properties, bills, payments, complaints, notices, reports, settings
# api_router.include_router(users.router)
# api_router.include_router(properties.router)
# ...

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.db.session import get_db
from app.core.dependencies import get_current_user, require_management, require_admin
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserResponse, UserListResponse
from app.services import user_service

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=UserListResponse, summary="List all users (Admin/Mgmt)")
def list_users(
    role:      Optional[str]  = Query(None),
    is_active: Optional[bool] = Query(None),
    skip:      int            = Query(0, ge=0),
    limit:     int            = Query(50, le=200),
    db:        Session        = Depends(get_db),
    _:         User           = Depends(require_management),
):
    return user_service.list_users(db, role=role, is_active=is_active, skip=skip, limit=limit)


@router.post("", response_model=UserResponse, status_code=201, summary="Create user (Admin)")
def create_user(
    payload: UserCreate,
    db:      Session = Depends(get_db),
    actor:   User    = Depends(require_admin),
):
    return user_service.create_user(db, payload, created_by_id=actor.user_id)


@router.get("/me", response_model=UserResponse, summary="Get own profile")
def get_me(
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    return user_service.get_user(db, current_user.user_id)


@router.get("/{user_id}", response_model=UserResponse, summary="Get user by ID (Admin/Mgmt)")
def get_user(
    user_id: int,
    db:      Session = Depends(get_db),
    _:       User    = Depends(require_management),
):
    return user_service.get_user(db, user_id)


@router.patch("/{user_id}", response_model=UserResponse, summary="Update user (Admin)")
def update_user(
    user_id: int,
    payload: UserUpdate,
    db:      Session = Depends(get_db),
    actor:   User    = Depends(require_admin),
):
    return user_service.update_user(db, user_id, payload, updated_by_id=actor.user_id)


@router.delete("/{user_id}", summary="Deactivate user (Admin)")
def deactivate_user(
    user_id: int,
    db:      Session = Depends(get_db),
    actor:   User    = Depends(require_admin),
):
    return user_service.delete_user(db, user_id, deleted_by_id=actor.user_id)

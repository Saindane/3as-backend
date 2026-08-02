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


@router.post("", response_model=UserResponse, status_code=201, summary="Create user (Mgmt/Admin)")
def create_user(
    payload: UserCreate,
    db:      Session = Depends(get_db),
    actor:   User    = Depends(require_management),
):
    return user_service.create_user(db, payload, created_by_id=actor.user_id)


@router.get("/me", response_model=UserResponse, summary="Get own profile")
def get_me(
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    return user_service.get_user(db, current_user.user_id)


@router.post("/me/change-password", summary="Change own password")
def change_password(
    payload:      dict,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    import bcrypt
    current_pw = payload.get("current_password", "")
    new_pw     = payload.get("new_password", "")

    if len(new_pw) < 6:
        from fastapi import HTTPException
        raise HTTPException(status_code=400,
            detail="New password must be at least 6 characters")

    # Verify current password
    if not bcrypt.checkpw(current_pw.encode(), current_user.password_hash.encode()):
        from fastapi import HTTPException
        raise HTTPException(status_code=400,
            detail="Current password is incorrect")

    return user_service.change_password(db, current_user.user_id, new_pw)


@router.get("/{user_id}", response_model=UserResponse, summary="Get user by ID (Admin/Mgmt)")
def get_user(
    user_id: int,
    db:      Session = Depends(get_db),
    _:       User    = Depends(require_management),
):
    return user_service.get_user(db, user_id)


@router.patch("/{user_id}", response_model=UserResponse, summary="Update user (Mgmt/Admin)")
def update_user(
    user_id: int,
    payload: UserUpdate,
    db:      Session = Depends(get_db),
    actor:   User    = Depends(require_management),  # management can edit users
):
    return user_service.update_user(db, user_id, payload, updated_by_id=actor.user_id)



@router.post("/{user_id}/reset-password", summary="Admin resets user password")
def admin_reset_password(
    user_id: int,
    payload: dict,
    db:      Session = Depends(get_db),
    actor:   User    = Depends(require_admin),
):
    from app.core.security import hash_password
    new_password = (payload.get("new_password") or "").strip()
    if len(new_password) < 6:
        raise HTTPException(status_code=400,
            detail="Password must be at least 6 characters")
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.password_hash = hash_password(new_password)
    db.commit()
    return {"message": f"Password reset successfully for {user.name}"}


@router.delete("/{user_id}", summary="Delete user (Admin only)")
def delete_user(
    user_id: int,
    db:      Session = Depends(get_db),
    actor:   User    = Depends(require_admin),  # only admin can hard delete
):
    return user_service.hard_delete_user(db, user_id, deleted_by_id=actor.user_id)

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.security import hash_password
from app.models.user import User
from app.models.property import Occupant
from app.models.audit_log import AuditLog
from app.schemas.user import UserCreate, UserUpdate


# ── CRUD ──────────────────────────────────────────────────────────

def create_user(db: Session, payload: UserCreate, created_by_id: int) -> User:
    if db.query(User).filter(User.mobile == payload.mobile).first():
        raise HTTPException(status_code=400, detail="Mobile number already registered")

    user = User(
        name=payload.name,
        mobile=payload.mobile,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=payload.role.upper(),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    _log(db, created_by_id, "USER_CREATED", entity_id=user.user_id,
         detail=f"role={user.role.upper()} mobile={user.mobile}")
    return user


def get_user(db: Session, user_id: int) -> User:
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def list_users(db: Session, role: str = None, is_active: bool = None,
               skip: int = 0, limit: int = 50):
    q = db.query(User)
    if role:
        q = q.filter(User.role == role.upper())
    if is_active is not None:
        q = q.filter(User.is_active == is_active)
    total = q.count()
    items = q.order_by(User.name).offset(skip).limit(limit).all()
    return {"total": total, "items": items}


def update_user(db: Session, user_id: int, payload: UserUpdate, updated_by_id: int) -> User:
    user = get_user(db, user_id)
    if payload.name      is not None: user.name      = payload.name
    if payload.email     is not None: user.email     = payload.email
    if payload.is_active is not None: user.is_active = payload.is_active
    if payload.role      is not None: user.role      = payload.role.upper()
    db.commit()
    db.refresh(user)
    _log(db, updated_by_id, "USER_UPDATED", entity_id=user_id)
    return user


def delete_user(db: Session, user_id: int, deleted_by_id: int):
    user = get_user(db, user_id)

    # Case 1: Block delete if user is attached to a property
    occupant = db.query(Occupant).filter(Occupant.user_id == user_id).first()
    if occupant:
        from app.models.property import Property
        prop = db.query(Property).filter(
            Property.property_id == occupant.property_id
        ).first()
        unit = prop.unit_no if prop else f"ID {occupant.property_id}"
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete user — they are attached to Unit {unit}. "
                   f"Please reassign or remove the unit owner first."
        )

    user.is_active = False          # soft delete
    db.commit()
    _log(db, deleted_by_id, "USER_DEACTIVATED", entity_id=user_id)
    return {"message": "User deleted successfully"}


def change_password(db: Session, user_id: int, new_password: str):
    user = get_user(db, user_id)
    user.password_hash = hash_password(new_password)
    db.commit()
    _log(db, user_id, "PASSWORD_CHANGED", entity_id=user_id)
    return {"message": "Password updated"}


# ── Private ───────────────────────────────────────────────────────

def _log(db: Session, user_id: int, action: str, entity: str = "User",
         entity_id: int = None, detail: str = None):
    db.add(AuditLog(user_id=user_id, action=action, entity=entity,
                    entity_id=entity_id, detail=detail))
    db.commit()


def hard_delete_user(db: Session, user_id: int, deleted_by_id: int):
    user = get_user(db, user_id)
    db.delete(user)
    db.commit()
    _log(db, deleted_by_id, "USER_DELETED", entity_id=user_id,
         detail=f"hard delete by user {deleted_by_id}")
    return {"message": "User deleted permanently"}

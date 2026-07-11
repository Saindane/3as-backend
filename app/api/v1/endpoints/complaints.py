from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.db.session import get_db
from app.core.dependencies import get_current_user, require_management, require_admin
from app.models.user import User, UserRole
from app.schemas.complaint import ComplaintCreateRequest, ComplaintUpdateRequest
from app.services import complaint_service

router = APIRouter(prefix="/complaints", tags=["Complaints"])


@router.get("", summary="List complaints — resident sees own, mgmt/admin sees all")
def list_complaints(
    status:   Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    skip:     int           = Query(0, ge=0),
    limit:    int           = Query(50, le=200),
    db:       Session       = Depends(get_db),
    current_user: User      = Depends(get_current_user),
):
    if current_user.role.upper() == 'RESIDENT':
        return complaint_service.get_my_complaints(db, current_user.user_id)
    return complaint_service.list_complaints(
        db, status=status, category=category,
        priority=priority, skip=skip, limit=limit,
    )


@router.post("", status_code=201, summary="Raise a new complaint")
def raise_complaint(
    payload:      ComplaintCreateRequest,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    return complaint_service.raise_complaint(db, payload, current_user.user_id)


@router.get("/{complaint_id}", summary="Get complaint by ID")
def get_complaint(
    complaint_id: int,
    db:           Session = Depends(get_db),
    _:            User    = Depends(get_current_user),
):
    return complaint_service.get_complaint(db, complaint_id)


@router.patch("/{complaint_id}", summary="Update complaint status / assign / resolve (Mgmt/Admin)")
def update_complaint(
    complaint_id: int,
    payload:      ComplaintUpdateRequest,
    db:           Session = Depends(get_db),
    actor:        User    = Depends(require_management),
):
    return complaint_service.update_complaint(db, complaint_id, payload, actor.user_id)


@router.delete("/{complaint_id}", summary="Delete complaint (Admin)")
def delete_complaint(
    complaint_id: int,
    db:           Session = Depends(get_db),
    actor:        User    = Depends(require_admin),
):
    return complaint_service.delete_complaint(db, complaint_id, actor.user_id)

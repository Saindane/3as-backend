from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.db.session import get_db
from app.core.dependencies import get_current_user, require_management, require_admin
from app.models.user import User, UserRole
from app.schemas.bill import (
    BillGenerateRequest, BillListResponse, BillResponse,
    GenerationResult, PenaltyPreview,
)
from app.services import bill_service

router = APIRouter(prefix="/bills", tags=["Bills"])


@router.get("", summary="List bills — resident sees own, admin/mgmt sees all")
def list_bills(
    property_id: Optional[int] = Query(None),
    status:      Optional[str] = Query(None),
    month:       Optional[int] = Query(None),
    year:        Optional[int] = Query(None),
    skip:        int           = Query(0, ge=0),
    limit:       int           = Query(50, le=200),
    db:          Session       = Depends(get_db),
    current_user: User         = Depends(get_current_user),
):
    # Residents only see their own bills
    if current_user.role.upper() == 'RESIDENT':
        return bill_service.get_bills_for_resident(db, current_user.user_id)

    # Admin / management can filter freely
    return bill_service.list_bills(
        db, property_id=property_id, status=status,
        month=month, year=year, skip=skip, limit=limit,
    )


@router.get("/my", summary="Get my bills (Resident only)")
def get_my_bills(
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    """Dedicated endpoint for residents to get their own bills only."""
    return bill_service.get_bills_for_resident(db, current_user.user_id)


@router.post(
    "/generate",
    response_model=GenerationResult,
    status_code=201,
    summary="Generate bills for all properties (Admin)",
)
def generate_bills(
    payload: BillGenerateRequest,
    db:      Session = Depends(get_db),
    actor:   User    = Depends(require_admin),
):
    return bill_service.generate_bills(db, payload, created_by_id=actor.user_id)


@router.get(
    "/penalties/preview",
    response_model=list[PenaltyPreview],
    summary="Preview penalties for all overdue bills (Admin/Mgmt)",
)
def preview_penalties(
    db: Session = Depends(get_db),
    _:  User    = Depends(require_management),
):
    return bill_service.preview_penalties(db)


@router.post(
    "/penalties/apply",
    summary="Manually trigger penalty recalculation (Admin)",
)
def apply_penalties(
    db:    Session = Depends(get_db),
    actor: User    = Depends(require_admin),
):
    updated = bill_service.apply_penalties_for_all(db)
    return {"message": f"Penalty applied to {updated} bills"}


@router.get(
    "/summary",
    summary="Collection summary for a month (Admin/Mgmt)",
)
def collection_summary(
    month: int = Query(..., ge=1, le=12),
    year:  int = Query(..., ge=2020),
    db:    Session = Depends(get_db),
    _:     User    = Depends(require_management),
):
    return bill_service.get_collection_summary(db, month, year)


@router.get("/{bill_id}", summary="Get single bill")
def get_bill(
    bill_id:     int,
    db:          Session = Depends(get_db),
    current_user: User   = Depends(get_current_user),
):
    bill = bill_service.get_bill(db, bill_id)
    return {
        "bill_id":     bill.bill_id,
        "property_id": bill.property_id,
        "unit_no":     bill.property.unit_no if bill.property else None,
        "month":       bill.month,
        "year":        bill.year,
        "maintenance": bill.maintenance,
        "penalty":     bill.penalty,
        "total":       bill.total,
        "due_date":    bill.due_date,
        "status":      bill.status.value,
        "created_at":  bill.created_at,
    }


@router.patch("/{bill_id}/waive", summary="Waive bill penalty (Admin)")
def waive_bill(
    bill_id: int,
    db:      Session = Depends(get_db),
    actor:   User    = Depends(require_admin),
):
    return bill_service.waive_bill(db, bill_id, waived_by_id=actor.user_id)

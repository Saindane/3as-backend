from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.db.session import get_db
from app.core.dependencies import get_current_user, require_management
from app.models.user import User, UserRole
from app.schemas.payment import PaymentSubmitRequest, PaymentVerifyRequest
from app.services import payment_service

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.get("", summary="List payments — resident sees own, mgmt/admin sees all")
def list_payments(
    status:  Optional[str] = Query(None),
    bill_id: Optional[int] = Query(None),
    skip:    int           = Query(0, ge=0),
    limit:   int           = Query(50, le=200),
    db:      Session       = Depends(get_db),
    current_user: User     = Depends(get_current_user),
):
    if current_user.role == UserRole.resident:
        return payment_service.get_payments_for_resident(db, current_user.user_id)
    return payment_service.list_payments(db, status=status, bill_id=bill_id,
                                         skip=skip, limit=limit)


@router.get("/pending", summary="All pending payments awaiting verification (Mgmt/Admin)")
def pending_payments(
    db: Session = Depends(get_db),
    _:  User    = Depends(require_management),
):
    return payment_service.get_pending_payments(db)


@router.post("", status_code=201, summary="Submit payment with UTR + screenshot")
def submit_payment(
    payload:      PaymentSubmitRequest,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    return payment_service.submit_payment(db, payload, current_user.user_id)


@router.patch("/{payment_id}/verify",
              summary="Verify or reject a payment (Mgmt/Admin)")
def verify_payment(
    payment_id: int,
    payload:    PaymentVerifyRequest,
    db:         Session = Depends(get_db),
    actor:      User    = Depends(require_management),
):
    return payment_service.verify_payment(db, payment_id, payload.action, actor.user_id)

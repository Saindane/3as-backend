from datetime import datetime, timezone
from typing import Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.payment import Payment, PaymentStatus, PaymentMode
from app.models.bill import Bill, BillStatus
from app.models.audit_log import AuditLog
from app.schemas.payment import PaymentSubmitRequest


def submit_payment(db: Session, payload: PaymentSubmitRequest, user_id: int) -> dict:
    bill = db.query(Bill).filter(Bill.bill_id == payload.bill_id).first()
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    if bill.status == BillStatus.PAID:
        raise HTTPException(status_code=400, detail="Bill already paid")

    payment = Payment(
        bill_id=payload.bill_id,
        amount=payload.amount,
        utr=payload.utr,
        screenshot=payload.screenshot,
        mode=PaymentMode(payload.mode),
        status=PaymentStatus.PENDING,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)

    _log(db, user_id, "PAYMENT_SUBMITTED",
         entity_id=payment.payment_id,
         detail=f"bill_id={payload.bill_id} amount={payload.amount} utr={payload.utr}")
    return _to_dict(payment)


def verify_payment(db: Session, payment_id: int, action: str, verified_by_id: int) -> dict:
    payment = _get_payment(db, payment_id)

    if action == "verify":
        payment.status      = PaymentStatus.VERIFIED
        payment.verified_by = verified_by_id
        payment.verified_at = datetime.now(timezone.utc)

        # Mark the bill as paid
        bill = db.query(Bill).filter(Bill.bill_id == payment.bill_id).first()
        if bill:
            bill.status = BillStatus.PAID

        _log(db, verified_by_id, "PAYMENT_VERIFIED", entity_id=payment_id)

    elif action == "reject":
        payment.status      = PaymentStatus.REJECTED
        payment.verified_by = verified_by_id
        payment.verified_at = datetime.now(timezone.utc)
        _log(db, verified_by_id, "PAYMENT_REJECTED", entity_id=payment_id)
    else:
        raise HTTPException(status_code=400, detail="Action must be 'verify' or 'reject'")

    db.commit()
    db.refresh(payment)
    return _to_dict(payment)


def list_payments(
    db: Session,
    status: Optional[str] = None,
    bill_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 50,
) -> dict:
    q = db.query(Payment)
    if status:
        q = q.filter(Payment.status == PaymentStatus(status))
    if bill_id:
        q = q.filter(Payment.bill_id == bill_id)

    total = q.count()
    items = q.order_by(Payment.created_at.desc()).offset(skip).limit(limit).all()
    return {"total": total, "items": [_to_dict(p) for p in items]}


def get_payments_for_resident(db: Session, user_id: int) -> dict:
    from app.models.property import Occupant
    occupant = db.query(Occupant).filter(Occupant.user_id == user_id).first()
    if not occupant:
        return {"total": 0, "items": []}

    bill_ids = [
        b.bill_id for b in
        db.query(Bill).filter(Bill.property_id == occupant.property_id).all()
    ]
    if not bill_ids:
        return {"total": 0, "items": []}

    q = db.query(Payment).filter(Payment.bill_id.in_(bill_ids))
    total = q.count()
    items = q.order_by(Payment.created_at.desc()).all()
    return {"total": total, "items": [_to_dict(p) for p in items]}


def get_pending_payments(db: Session) -> dict:
    q = db.query(Payment).filter(Payment.status == PaymentStatus.PENDING)
    total = q.count()
    items = q.order_by(Payment.created_at.asc()).all()
    return {"total": total, "items": [_to_dict(p) for p in items]}


def _get_payment(db: Session, payment_id: int) -> Payment:
    p = db.query(Payment).filter(Payment.payment_id == payment_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Payment not found")
    return p


def _to_dict(p: Payment) -> dict:
    unit_no = None
    if p.bill and p.bill.property:
        unit_no = p.bill.property.unit_no
    return {
        "payment_id":  p.payment_id,
        "bill_id":     p.bill_id,
        "amount":      p.amount,
        "utr":         p.utr,
        "screenshot":  p.screenshot,
        "mode":        p.mode.value,
        "status":      p.status.value,
        "verified_by": p.verified_by,
        "verified_at": p.verified_at,
        "created_at":  p.created_at,
        "unit_no":     unit_no,
    }


def _log(db, user_id, action, entity="Payment", entity_id=None, detail=None):
    db.add(AuditLog(user_id=user_id, action=action, entity=entity,
                    entity_id=entity_id, detail=detail))
    db.commit()

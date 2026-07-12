"""
Bill generation + Penalty engine
=================================
Penalty formula:
    Penalty = Outstanding × Daily_Penalty_% × Days_Overdue

Daily_Penalty_% is stored in the settings table under key 'penalty_daily_pct'.
Default is 0.05 (i.e. 0.05% per day).

The penalty cron job (APScheduler) calls `apply_penalties_for_all()` every night at 00:05.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timezone
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.bill import Bill, BillStatus
from app.models.property import Property
from app.models.audit_log import AuditLog
from app.schemas.bill import BillGenerateRequest, GenerationResult, PenaltyPreview

logger = logging.getLogger(__name__)

# ── Settings helpers ──────────────────────────────────────────────

def _get_setting(db: Session, key: str, default: str) -> str:
    from app.models.setting import Setting  # local import to avoid circular
    row = db.query(Setting).filter(Setting.key == key).first()
    return row.value if row else default


def get_daily_penalty_pct(db: Session) -> float:
    """Returns the daily penalty percentage as a float (e.g. 0.05 for 0.05%)."""
    raw = _get_setting(db, "penalty_daily_pct", "0.05")
    try:
        return float(raw)
    except ValueError:
        return 0.05


# ── Bill generation ───────────────────────────────────────────────

def generate_bills(
    db: Session,
    payload: BillGenerateRequest,
    created_by_id: int,
) -> GenerationResult:
    """
    Generate one bill per active property for the given month/year.
    Skips properties that already have a bill for that period.
    """
    properties = db.query(Property).all()
    generated = 0
    skipped   = 0
    details: List[str] = []
    total_amount = 0.0

    for prop in properties:
        # Skip if bill already exists for this period
        exists = db.query(Bill).filter(
            Bill.property_id == prop.property_id,
            Bill.month == payload.month,
            Bill.year  == payload.year,
        ).first()

        if exists:
            skipped += 1
            details.append(f"Unit {prop.unit_no}: skipped (bill already exists)")
            continue

        # Calculate penalty if requested
        penalty = 0.0
        if payload.include_penalty:
            penalty = _calculate_pending_penalty(db, prop.property_id)

        total = payload.maintenance + penalty

        bill = Bill(
            property_id=prop.property_id,
            month=payload.month,
            year=payload.year,
            maintenance=payload.maintenance,
            penalty=round(penalty, 2),
            total=round(total, 2),
            due_date=payload.due_date,
            status=BillStatus.PENDING,
        )
        db.add(bill)
        generated   += 1
        total_amount += total
        details.append(
            f"Unit {prop.unit_no}: ₹{payload.maintenance:.0f} + ₹{penalty:.2f} penalty = ₹{total:.2f}"
        )

    db.commit()
    _log(db, created_by_id, "BILLS_GENERATED",
         detail=f"month={payload.month}/{payload.year} generated={generated}")

    return GenerationResult(
        generated=generated,
        skipped=skipped,
        total_amount=round(total_amount, 2),
        details=details,
    )


# ── Penalty engine ────────────────────────────────────────────────

def apply_penalties_for_all(db: Session) -> int:
    """
    Nightly cron: find all PENDING/OVERDUE bills past due_date,
    recalculate penalty and update bill totals.
    Returns number of bills updated.
    """
    today       = date.today()
    daily_rate  = get_daily_penalty_pct(db)
    updated     = 0

    overdue_bills = db.query(Bill).filter(
        Bill.status.in_([BillStatus.PENDING, BillStatus.OVERDUE]),
        Bill.due_date < today,
    ).all()

    for bill in overdue_bills:
        days_overdue = (today - bill.due_date).days
        penalty      = round(bill.maintenance * (daily_rate / 100) * days_overdue, 2)

        if penalty != bill.penalty:
            bill.penalty = penalty
            bill.total   = round(bill.maintenance + penalty, 2)
            bill.status  = BillStatus.OVERDUE
            updated += 1

    if updated:
        db.commit()
        logger.info(f"[PenaltyCron] Updated {updated} bills on {today}")

    return updated


def preview_penalties(db: Session) -> List[PenaltyPreview]:
    """Preview what penalties would look like for all overdue bills (without applying)."""
    today      = date.today()
    daily_rate = get_daily_penalty_pct(db)

    overdue = db.query(Bill).filter(
        Bill.status.in_([BillStatus.PENDING, BillStatus.OVERDUE]),
        Bill.due_date < today,
    ).all()

    previews = []
    for bill in overdue:
        days_overdue = (today - bill.due_date).days
        penalty      = round(bill.maintenance * (daily_rate / 100) * days_overdue, 2)
        unit_no      = bill.property.unit_no if bill.property else "?"

        previews.append(PenaltyPreview(
            property_id=bill.property_id,
            unit_no=unit_no,
            outstanding=bill.maintenance,
            daily_rate_pct=daily_rate,
            days_overdue=days_overdue,
            penalty_amount=penalty,
            formula=(
                f"₹{bill.maintenance:.0f} × {daily_rate}% × {days_overdue} days"
                f" = ₹{penalty:.2f}"
            ),
        ))

    return previews


# ── Bill queries ──────────────────────────────────────────────────

def list_bills(
    db: Session,
    property_id: Optional[int] = None,
    status: Optional[str]       = None,
    month: Optional[int]        = None,
    year: Optional[int]         = None,
    skip: int = 0,
    limit: int = 50,
) -> dict:
    q = db.query(Bill)
    if property_id: q = q.filter(Bill.property_id == property_id)
    if status:      q = q.filter(Bill.status == BillStatus(status.upper()))
    if month:       q = q.filter(Bill.month == month)
    if year:        q = q.filter(Bill.year  == year)

    total = q.count()
    items = q.order_by(Bill.year.desc(), Bill.month.desc()).offset(skip).limit(limit).all()

    # Attach unit_no for convenience
    result = []
    for bill in items:
        d = {
            "bill_id":     bill.bill_id,
            "property_id": bill.property_id,
            "unit_no":     bill.property.unit_no if bill.property else None,
            "month":       bill.month,
            "year":        bill.year,
            "maintenance": bill.maintenance,
            "penalty":     bill.penalty,
            "total":       bill.total,
            "due_date":    bill.due_date.isoformat() if bill.due_date else None,
            "status":      bill.status.value,
            "created_at":  bill.created_at.isoformat() if bill.created_at else None,
        }
        result.append(d)

    return {"total": total, "items": result}


def get_bill(db: Session, bill_id: int) -> Bill:
    bill = db.query(Bill).filter(Bill.bill_id == bill_id).first()
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    return bill


def get_bills_for_resident(db: Session, user_id: int) -> dict:
    """Get all bills for the property linked to this resident."""
    from app.models.property import Occupant
    occupant = db.query(Occupant).filter(Occupant.user_id == user_id).first()
    if not occupant:
        return {"total": 0, "items": []}
    return list_bills(db, property_id=occupant.property_id)


def waive_bill(db: Session, bill_id: int, waived_by_id: int) -> Bill:
    bill = get_bill(db, bill_id)
    bill.status  = BillStatus.WAIVED
    bill.penalty = 0.0
    bill.total   = bill.maintenance
    db.commit()
    db.refresh(bill)
    _log(db, waived_by_id, "BILL_WAIVED", entity_id=bill_id)
    return bill


def get_collection_summary(db: Session, month: int, year: int) -> dict:
    """Collection stats for a given month."""
    bills = db.query(Bill).filter(Bill.month == month, Bill.year == year).all()

    total_units   = len(bills)
    paid_amount   = sum(b.total for b in bills if b.status == BillStatus.PAID)
    pending_amount= sum(b.total for b in bills if b.status in (BillStatus.PENDING, BillStatus.OVERDUE))
    paid_count    = sum(1 for b in bills if b.status == BillStatus.PAID)
    pending_count = sum(1 for b in bills if b.status in (BillStatus.PENDING, BillStatus.OVERDUE))
    overdue_count = sum(1 for b in bills if b.status == BillStatus.OVERDUE)

    return {
        "month": month, "year": year,
        "total_bills": total_units,
        "paid_count": paid_count,
        "pending_count": pending_count,
        "overdue_count": overdue_count,
        "paid_amount": round(paid_amount, 2),
        "pending_amount": round(pending_amount, 2),
        "collection_pct": round(paid_amount / (paid_amount + pending_amount) * 100, 1)
            if (paid_amount + pending_amount) > 0 else 0.0,
    }


# ── Private helpers ───────────────────────────────────────────────

def _calculate_pending_penalty(db: Session, property_id: int) -> float:
    """Sum up outstanding penalties from any existing overdue bills."""
    overdue = db.query(Bill).filter(
        Bill.property_id == property_id,
        Bill.status.in_([BillStatus.PENDING, BillStatus.OVERDUE]),
    ).all()
    return sum(b.penalty for b in overdue)


def _log(db: Session, user_id: int, action: str, entity: str = "Bill",
         entity_id: int = None, detail: str = None):
    db.add(AuditLog(user_id=user_id, action=action, entity=entity,
                    entity_id=entity_id, detail=detail))
    db.commit()

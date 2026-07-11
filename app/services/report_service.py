from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.bill import Bill, BillStatus
from app.models.payment import Payment, PaymentStatus
from app.models.complaint import Complaint, ComplaintStatus
from app.models.audit_log import AuditLog
from app.models.user import User
from app.models.property import Property


def collection_report(db: Session, month: int, year: int) -> dict:
    bills = db.query(Bill).filter(Bill.month == month, Bill.year == year).all()
    result = []
    for b in bills:
        unit_no = b.property.unit_no if b.property else "?"
        owner   = b.property.owner.name if (b.property and b.property.owner) else "?"
        result.append({
            "bill_id":     b.bill_id,
            "unit_no":     unit_no,
            "owner":       owner,
            "maintenance": b.maintenance,
            "penalty":     b.penalty,
            "total":       b.total,
            "status":      b.status.value,
            "due_date":    b.due_date,
        })

    paid_total    = sum(b["total"] for b in result if b["status"] == "PAID")
    pending_total = sum(b["total"] for b in result if b["status"] in ("PENDING", "OVERDUE"))

    return {
        "month": month, "year": year,
        "total_bills":     len(result),
        "paid_count":      sum(1 for b in result if b["status"] == "PAID"),
        "pending_count":   sum(1 for b in result if b["status"] in ("PENDING", "OVERDUE")),
        "overdue_count":   sum(1 for b in result if b["status"] == "OVERDUE"),
        "paid_amount":     round(paid_total, 2),
        "pending_amount":  round(pending_total, 2),
        "collection_pct":  round(paid_total / (paid_total + pending_total) * 100, 1)
                           if (paid_total + pending_total) > 0 else 0.0,
        "bills": result,
    }


def defaulter_report(db: Session) -> dict:
    bills = db.query(Bill).filter(
        Bill.status.in_([BillStatus.PENDING, BillStatus.OVERDUE])
    ).order_by(Bill.year.desc(), Bill.month.desc()).all()

    result = []
    for b in bills:
        unit_no = b.property.unit_no if b.property else "?"
        owner   = b.property.owner.name if (b.property and b.property.owner) else "?"
        mobile  = b.property.owner.mobile if (b.property and b.property.owner) else ""
        result.append({
            "bill_id":     b.bill_id,
            "unit_no":     unit_no,
            "owner":       owner,
            "mobile":      mobile,
            "month":       b.month,
            "year":        b.year,
            "maintenance": b.maintenance,
            "penalty":     b.penalty,
            "total":       b.total,
            "status":      b.status.value,
            "due_date":    b.due_date,
        })

    return {
        "total_defaulters": len(result),
        "total_outstanding": round(sum(b["total"] for b in result), 2),
        "defaulters": result,
    }


def complaint_analytics(db: Session) -> dict:
    from app.models.complaint import ComplaintCategory
    total     = db.query(Complaint).count()
    open_c    = db.query(Complaint).filter(
        Complaint.status.notin_([ComplaintStatus.RESOLVED, ComplaintStatus.CLOSED])
    ).count()
    resolved  = db.query(Complaint).filter(
        Complaint.status.in_([ComplaintStatus.RESOLVED, ComplaintStatus.CLOSED])
    ).count()

    by_category = []
    for cat in ComplaintCategory:
        ct = db.query(Complaint).filter(Complaint.category == cat).count()
        op = db.query(Complaint).filter(
            Complaint.category == cat,
            Complaint.status.notin_([ComplaintStatus.RESOLVED, ComplaintStatus.CLOSED])
        ).count()
        if ct > 0:
            by_category.append({
                "category": cat.value,
                "total": ct,
                "open": op,
                "resolved": ct - op,
            })

    return {
        "total": total,
        "open": open_c,
        "resolved": resolved,
        "by_category": by_category,
    }


def audit_log_report(db: Session, user_id: int = None,
                     action: str = None, skip: int = 0, limit: int = 100) -> dict:
    q = db.query(AuditLog)
    if user_id: q = q.filter(AuditLog.user_id == user_id)
    if action:  q = q.filter(AuditLog.action  == action)

    total = q.count()
    items = q.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()

    return {
        "total": total,
        "items": [{
            "log_id":     l.log_id,
            "user_id":    l.user_id,
            "action":     l.action,
            "entity":     l.entity,
            "entity_id":  l.entity_id,
            "detail":     l.detail,
            "ip_address": l.ip_address,
            "created_at": l.created_at,
        } for l in items],
    }

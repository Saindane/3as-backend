from typing import Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.complaint import Complaint, ComplaintStatus, ComplaintCategory, ComplaintPriority
from app.models.property import Occupant
from app.models.audit_log import AuditLog
from app.schemas.complaint import ComplaintCreateRequest, ComplaintUpdateRequest


def raise_complaint(db: Session, payload: ComplaintCreateRequest, user_id: int) -> dict:
    # Find the user's property
    occupant = db.query(Occupant).filter(Occupant.user_id == user_id).first()
    property_id = occupant.property_id if occupant else None

    complaint = Complaint(
        property_id=property_id,
        raised_by=user_id,
        category=ComplaintCategory(payload.category.upper()),
        priority=ComplaintPriority(payload.priority.upper()),
        status=ComplaintStatus.NEW,
        title=payload.title,
        description=payload.description,
    )
    db.add(complaint)
    db.commit()
    db.refresh(complaint)
    _log(db, user_id, "COMPLAINT_RAISED", entity_id=complaint.complaint_id,
         detail=f"category={payload.category} priority={payload.priority}")
    return _to_dict(complaint)


def update_complaint(db: Session, complaint_id: int,
                     payload: ComplaintUpdateRequest, updated_by: int) -> dict:
    complaint = _get(db, complaint_id)

    if payload.status      is not None:
        complaint.status      = ComplaintStatus(payload.status.upper())
    if payload.assigned_to is not None:
        complaint.assigned_to = payload.assigned_to
        if complaint.status == ComplaintStatus.NEW:
            complaint.status = ComplaintStatus.ASSIGNED
    if payload.resolution  is not None:
        complaint.resolution  = payload.resolution
        complaint.status      = ComplaintStatus.RESOLVED
    if payload.priority    is not None:
        complaint.priority    = ComplaintPriority(payload.priority.upper())

    db.commit()
    db.refresh(complaint)
    _log(db, updated_by, "COMPLAINT_UPDATED", entity_id=complaint_id)
    return _to_dict(complaint)


def list_complaints(
    db: Session,
    status: Optional[str]   = None,
    category: Optional[str] = None,
    priority: Optional[str] = None,
    property_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 50,
) -> dict:
    q = db.query(Complaint)
    if status:      q = q.filter(Complaint.status   == ComplaintStatus(status))
    if category:    q = q.filter(Complaint.category == ComplaintCategory(category))
    if priority:    q = q.filter(Complaint.priority == ComplaintPriority(priority))
    if property_id: q = q.filter(Complaint.property_id == property_id)

    total = q.count()
    items = q.order_by(Complaint.created_at.desc()).offset(skip).limit(limit).all()
    return {"total": total, "items": [_to_dict(c) for c in items]}


def get_my_complaints(db: Session, user_id: int) -> dict:
    q = db.query(Complaint).filter(Complaint.raised_by == user_id)
    total = q.count()
    items = q.order_by(Complaint.created_at.desc()).all()
    return {"total": total, "items": [_to_dict(c) for c in items]}


def get_complaint(db: Session, complaint_id: int) -> dict:
    return _to_dict(_get(db, complaint_id))


def delete_complaint(db: Session, complaint_id: int, deleted_by: int):
    complaint = _get(db, complaint_id)
    db.delete(complaint)
    db.commit()
    _log(db, deleted_by, "COMPLAINT_DELETED", entity_id=complaint_id)
    return {"message": "Complaint deleted"}


def _get(db, complaint_id):
    c = db.query(Complaint).filter(Complaint.complaint_id == complaint_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return c


def _to_dict(c: Complaint) -> dict:
    return {
        "complaint_id": c.complaint_id,
        "property_id":  c.property_id,
        "raised_by":    c.raised_by,
        "assigned_to":  c.assigned_to,
        "category":     c.category.value,
        "priority":     c.priority.value,
        "status":       c.status.value,
        "title":        c.title,
        "description":  c.description,
        "resolution":   c.resolution,
        "created_at":   c.created_at,
        "updated_at":   c.updated_at,
        "unit_no":      c.property.unit_no if c.property else None,
        "raiser_name":  c.raiser.name if c.raiser else None,
    }


def _log(db, user_id, action, entity="Complaint", entity_id=None, detail=None):
    db.add(AuditLog(user_id=user_id, action=action, entity=entity,
                    entity_id=entity_id, detail=detail))
    db.commit()

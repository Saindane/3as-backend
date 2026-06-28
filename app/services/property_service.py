from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.property import Property, Occupant, OccupancyType, PropertyType
from app.models.audit_log import AuditLog
from app.schemas.property import PropertyCreate, PropertyUpdate, OccupantCreate, DashboardStats
from app.models.user import User


def create_property(db: Session, payload: PropertyCreate, created_by_id: int) -> Property:
    if db.query(Property).filter(Property.unit_no == payload.unit_no).first():
        raise HTTPException(status_code=400, detail=f"Unit {payload.unit_no} already exists")

    prop = Property(
        unit_no=payload.unit_no,
        floor=payload.floor,
        type=PropertyType(payload.type),
        area_sqft=payload.area_sqft,
        owner_id=payload.owner_id,
    )
    db.add(prop)
    db.commit()
    db.refresh(prop)

    # Auto-create occupant record if owner_id given
    if payload.owner_id:
        _add_occupant(db, prop.property_id, payload.owner_id, "owner")

    _log(db, created_by_id, "PROPERTY_CREATED", entity_id=prop.property_id,
         detail=f"unit={prop.unit_no}")
    return prop


def get_property(db: Session, property_id: int) -> Property:
    prop = db.query(Property).filter(Property.property_id == property_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    return prop


def list_properties(db: Session, floor: int = None, skip: int = 0, limit: int = 100):
    q = db.query(Property)
    if floor is not None:
        q = q.filter(Property.floor == floor)
    total = q.count()
    items = q.order_by(Property.unit_no).offset(skip).limit(limit).all()
    return {"total": total, "items": items}


def update_property(db: Session, property_id: int, payload: PropertyUpdate,
                    updated_by_id: int) -> Property:
    prop = get_property(db, property_id)
    if payload.unit_no   is not None: prop.unit_no   = payload.unit_no
    if payload.floor     is not None: prop.floor     = payload.floor
    if payload.type      is not None: prop.type      = PropertyType(payload.type)
    if payload.area_sqft is not None: prop.area_sqft = payload.area_sqft
    if payload.owner_id  is not None:
        prop.owner_id = payload.owner_id
        _add_occupant(db, property_id, payload.owner_id, "owner")
    db.commit()
    db.refresh(prop)
    _log(db, updated_by_id, "PROPERTY_UPDATED", entity_id=property_id)
    return prop


def delete_property(db: Session, property_id: int, deleted_by_id: int):
    prop = get_property(db, property_id)
    db.delete(prop)
    db.commit()
    _log(db, deleted_by_id, "PROPERTY_DELETED", entity_id=property_id,
         detail=f"unit={prop.unit_no}")
    return {"message": "Property deleted"}


def add_occupant(db: Session, property_id: int, payload: OccupantCreate,
                 added_by_id: int) -> Occupant:
    get_property(db, property_id)           # ensure exists
    return _add_occupant(db, property_id, payload.user_id, payload.occupancy_type)


def get_resident_property(db: Session, user_id: int):
    """Return the property a resident is linked to."""
    occupant = (db.query(Occupant)
                .filter(Occupant.user_id == user_id)
                .first())
    if not occupant:
        return None
    return get_property(db, occupant.property_id)


def get_dashboard_stats(db: Session, user_id: int = None) -> DashboardStats:
    """Aggregate stats for the admin/mgmt dashboard."""
    from app.models.bill import Bill, BillStatus          # imported here to avoid circular
    from app.models.complaint import Complaint, ComplaintStatus

    total_units   = db.query(Property).count()
    total_users   = db.query(User).count()
    active_users  = db.query(User).filter(User.is_active == True).count()
    bills_paid    = db.query(Bill).filter(Bill.status == BillStatus.PAID).count()
    bills_pending = db.query(Bill).filter(Bill.status == BillStatus.PENDING).count()
    open_comp     = db.query(Complaint).filter(
        Complaint.status.notin_([ComplaintStatus.RESOLVED, ComplaintStatus.CLOSED])
    ).count()

    from sqlalchemy import func as sqlfunc
    coll = db.query(sqlfunc.coalesce(sqlfunc.sum(Bill.total), 0)).filter(
        Bill.status == BillStatus.PAID).scalar()
    pend = db.query(sqlfunc.coalesce(sqlfunc.sum(Bill.total), 0)).filter(
        Bill.status == BillStatus.PENDING).scalar()

    return DashboardStats(
        total_units=total_units,
        total_users=total_users,
        active_users=active_users,
        bills_paid=bills_paid,
        bills_pending=bills_pending,
        open_complaints=open_comp,
        unread_notices=0,
        collection_amount=float(coll or 0),
        pending_amount=float(pend or 0),
    )


# ── Private ───────────────────────────────────────────────────────

def _add_occupant(db, property_id, user_id, occupancy_type):
    existing = db.query(Occupant).filter(
        Occupant.property_id == property_id,
        Occupant.user_id == user_id
    ).first()
    if existing:
        existing.occupancy_type = OccupancyType(occupancy_type)
        db.commit()
        return existing
    occ = Occupant(property_id=property_id, user_id=user_id,
                   occupancy_type=OccupancyType(occupancy_type))
    db.add(occ)
    db.commit()
    db.refresh(occ)
    return occ


def _log(db, user_id, action, entity="Property", entity_id=None, detail=None):
    db.add(AuditLog(user_id=user_id, action=action, entity=entity,
                    entity_id=entity_id, detail=detail))
    db.commit()

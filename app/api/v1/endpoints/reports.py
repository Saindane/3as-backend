from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.db.session import get_db
from app.core.dependencies import require_management, require_admin
from app.models.user import User
from app.services import report_service

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/collection",
            summary="Monthly collection report (Mgmt/Admin)")
def collection_report(
    month: int     = Query(..., ge=1, le=12),
    year:  int     = Query(..., ge=2020),
    db:    Session = Depends(get_db),
    _:     User    = Depends(require_management),
):
    return report_service.collection_report(db, month, year)


@router.get("/defaulters",
            summary="Defaulter list — all unpaid/overdue bills (Mgmt/Admin)")
def defaulter_report(
    db: Session = Depends(get_db),
    _:  User    = Depends(require_management),
):
    return report_service.defaulter_report(db)


@router.get("/complaints",
            summary="Complaint analytics by category (Mgmt/Admin)")
def complaint_analytics(
    db: Session = Depends(get_db),
    _:  User    = Depends(require_management),
):
    return report_service.complaint_analytics(db)


@router.get("/audit-logs",
            summary="Audit log report (Admin only)")
def audit_log_report(
    user_id: Optional[int] = Query(None),
    action:  Optional[str] = Query(None),
    skip:    int           = Query(0, ge=0),
    limit:   int           = Query(100, le=500),
    db:      Session       = Depends(get_db),
    _:       User          = Depends(require_admin),
):
    return report_service.audit_log_report(db, user_id=user_id, action=action,
                                           skip=skip, limit=limit)

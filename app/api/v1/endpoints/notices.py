from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.dependencies import get_current_user, require_management, require_admin
from app.models.user import User
from app.schemas.notice import NoticeCreateRequest, NoticeUpdateRequest
from app.services import notice_service

router = APIRouter(prefix="/notices", tags=["Notices"])


@router.get("", summary="List active notices (all authenticated users)")
def list_notices(
    active_only: bool = Query(True),
    skip:        int  = Query(0, ge=0),
    limit:       int  = Query(50, le=200),
    db:          Session = Depends(get_db),
    _:           User    = Depends(get_current_user),
):
    return notice_service.list_notices(db, active_only=active_only,
                                       skip=skip, limit=limit)


@router.post("", status_code=201,
             summary="Publish a notice (Mgmt/Admin) — sends FCM push")
def create_notice(
    payload: NoticeCreateRequest,
    db:      Session = Depends(get_db),
    actor:   User    = Depends(require_management),
):
    result = notice_service.create_notice(db, payload, actor.user_id)
    # FCM push placeholder — wire Firebase Admin SDK here in production
    print(f"[FCM] Push sent for notice: {payload.title}")
    return result


@router.get("/{notice_id}", summary="Get notice by ID")
def get_notice(
    notice_id: int,
    db:        Session = Depends(get_db),
    _:         User    = Depends(get_current_user),
):
    return notice_service.get_notice(db, notice_id)


@router.patch("/{notice_id}", summary="Update notice (Mgmt/Admin)")
def update_notice(
    notice_id: int,
    payload:   NoticeUpdateRequest,
    db:        Session = Depends(get_db),
    actor:     User    = Depends(require_management),
):
    return notice_service.update_notice(db, notice_id, payload, actor.user_id)


@router.delete("/{notice_id}", summary="Deactivate notice (Admin)")
def delete_notice(
    notice_id: int,
    db:        Session = Depends(get_db),
    actor:     User    = Depends(require_admin),
):
    return notice_service.delete_notice(db, notice_id, actor.user_id)

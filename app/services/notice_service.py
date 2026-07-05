from typing import Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.notice import Notice
from app.models.audit_log import AuditLog
from app.schemas.notice import NoticeCreateRequest, NoticeUpdateRequest


def create_notice(db: Session, payload: NoticeCreateRequest, created_by: int) -> dict:
    notice = Notice(
        title=payload.title,
        body=payload.body,
        category=payload.category,
        priority=payload.priority,
        created_by=created_by,
        is_active=True,
    )
    db.add(notice)
    db.commit()
    db.refresh(notice)
    _log(db, created_by, "NOTICE_PUBLISHED", entity_id=notice.notice_id,
         detail=f"title={payload.title}")
    return _to_dict(notice)


def list_notices(
    db: Session,
    active_only: bool = True,
    skip: int = 0,
    limit: int = 50,
) -> dict:
    q = db.query(Notice)
    if active_only:
        q = q.filter(Notice.is_active == True)
    total = q.count()
    items = q.order_by(Notice.created_at.desc()).offset(skip).limit(limit).all()
    return {"total": total, "items": [_to_dict(n) for n in items]}


def get_notice(db: Session, notice_id: int) -> dict:
    return _to_dict(_get(db, notice_id))


def update_notice(db: Session, notice_id: int,
                  payload: NoticeUpdateRequest, updated_by: int) -> dict:
    notice = _get(db, notice_id)
    if payload.title     is not None: notice.title     = payload.title
    if payload.body      is not None: notice.body      = payload.body
    if payload.category  is not None: notice.category  = payload.category
    if payload.priority  is not None: notice.priority  = payload.priority
    if payload.is_active is not None: notice.is_active = payload.is_active
    db.commit()
    db.refresh(notice)
    _log(db, updated_by, "NOTICE_UPDATED", entity_id=notice_id)
    return _to_dict(notice)


def delete_notice(db: Session, notice_id: int, deleted_by: int):
    notice = _get(db, notice_id)
    notice.is_active = False
    db.commit()
    _log(db, deleted_by, "NOTICE_DELETED", entity_id=notice_id)
    return {"message": "Notice deactivated"}


def _get(db, notice_id):
    n = db.query(Notice).filter(Notice.notice_id == notice_id).first()
    if not n:
        raise HTTPException(status_code=404, detail="Notice not found")
    return n


def _to_dict(n: Notice) -> dict:
    return {
        "notice_id":   n.notice_id,
        "title":       n.title,
        "body":        n.body,
        "category":    n.category,
        "priority":    n.priority,
        "is_active":   n.is_active,
        "created_by":  n.created_by,
        "author_name": n.author.name if n.author else None,
        "created_at":  n.created_at,
    }


def _log(db, user_id, action, entity="Notice", entity_id=None, detail=None):
    db.add(AuditLog(user_id=user_id, action=action, entity=entity,
                    entity_id=entity_id, detail=detail))
    db.commit()

from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.setting import Setting


def get_all_settings(db: Session) -> list:
    return db.query(Setting).order_by(Setting.key).all()


def get_setting(db: Session, key: str) -> Setting:
    s = db.query(Setting).filter(Setting.key == key).first()
    if not s:
        raise HTTPException(status_code=404, detail=f"Setting '{key}' not found")
    return s


def update_setting(db: Session, key: str, value: str) -> Setting:
    s = db.query(Setting).filter(Setting.key == key).first()
    if s:
        s.value = value
    else:
        s = Setting(key=key, value=value)
        db.add(s)
    db.commit()
    db.refresh(s)
    return s


def delete_setting(db: Session, key: str):
    s = get_setting(db, key)
    db.delete(s)
    db.commit()
    return {"message": f"Setting '{key}' deleted"}

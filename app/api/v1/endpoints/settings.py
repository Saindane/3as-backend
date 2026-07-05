from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.dependencies import get_current_user, require_admin
from app.models.user import User
from app.schemas.setting import SettingResponse, SettingUpdateRequest, SettingsListResponse
from app.services import setting_service

router = APIRouter(prefix="/settings", tags=["Settings"])


@router.get("", response_model=SettingsListResponse,
            summary="Get all settings (Admin)")
def get_all_settings(
    db: Session = Depends(get_db),
    _:  User    = Depends(require_admin),
):
    items = setting_service.get_all_settings(db)
    return {"items": items}


@router.get("/{key}", response_model=SettingResponse,
            summary="Get a single setting")
def get_setting(
    key: str,
    db:  Session = Depends(get_db),
    _:   User    = Depends(get_current_user),
):
    return setting_service.get_setting(db, key)


@router.patch("/{key}", response_model=SettingResponse,
              summary="Update a setting value (Admin)")
def update_setting(
    key:     str,
    payload: SettingUpdateRequest,
    db:      Session = Depends(get_db),
    _:       User    = Depends(require_admin),
):
    return setting_service.update_setting(db, key, payload.value)


@router.delete("/{key}", summary="Delete a setting (Admin)")
def delete_setting(
    key: str,
    db:  Session = Depends(get_db),
    _:   User    = Depends(require_admin),
):
    return setting_service.delete_setting(db, key)

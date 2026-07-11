from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.db.session import get_db
from app.core.dependencies import get_current_user, require_management, require_admin
from app.models.user import User
from app.schemas.property import (
    PropertyCreate, PropertyUpdate, PropertyResponse,
    PropertyListResponse, OccupantCreate, OccupantResponse, DashboardStats
)
from app.services import property_service

router = APIRouter(prefix="/properties", tags=["Properties"])


@router.get("", response_model=PropertyListResponse, summary="List all properties")
def list_properties(
    floor: Optional[int] = Query(None),
    skip:  int           = Query(0, ge=0),
    limit: int           = Query(100, le=500),
    db:    Session       = Depends(get_db),
    _:     User          = Depends(get_current_user),
):
    return property_service.list_properties(db, floor=floor, skip=skip, limit=limit)


@router.post("", response_model=PropertyResponse, status_code=201, summary="Add property (Admin)")
def create_property(
    payload: PropertyCreate,
    db:      Session = Depends(get_db),
    actor:   User    = Depends(require_management),
):
    return property_service.create_property(db, payload, created_by_id=actor.user_id)


@router.get("/my", response_model=Optional[PropertyResponse], summary="Get my property (Resident)")
def get_my_property(
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    return property_service.get_resident_property(db, current_user.user_id)


@router.get("/dashboard", response_model=DashboardStats, summary="Dashboard stats (Admin/Mgmt)")
def dashboard_stats(
    db: Session = Depends(get_db),
    _:  User    = Depends(require_management),
):
    return property_service.get_dashboard_stats(db)


@router.get("/{property_id}", response_model=PropertyResponse, summary="Get property by ID")
def get_property(
    property_id: int,
    db:          Session = Depends(get_db),
    _:           User    = Depends(get_current_user),
):
    return property_service.get_property(db, property_id)


@router.patch("/{property_id}", response_model=PropertyResponse, summary="Update property (Admin)")
def update_property(
    property_id: int,
    payload:     PropertyUpdate,
    db:          Session = Depends(get_db),
    actor:       User    = Depends(require_admin),
):
    return property_service.update_property(db, property_id, payload,
                                            updated_by_id=actor.user_id)


@router.delete("/{property_id}", summary="Delete property (Mgmt/Admin)")
def delete_property(
    property_id: int,
    db:          Session = Depends(get_db),
    actor:       User    = Depends(require_management),
):
    return property_service.delete_property(db, property_id, deleted_by_id=actor.user_id)


@router.post("/{property_id}/occupants", response_model=OccupantResponse,
             status_code=201, summary="Add occupant to property")
def add_occupant(
    property_id: int,
    payload:     OccupantCreate,
    db:          Session = Depends(get_db),
    actor:       User    = Depends(require_management),
):
    return property_service.add_occupant(db, property_id, payload, added_by_id=actor.user_id)

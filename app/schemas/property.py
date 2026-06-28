from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class PropertyCreate(BaseModel):
    unit_no:   str
    floor:     int
    type:      str = "residential"
    area_sqft: Optional[float] = None
    owner_id:  Optional[int]   = None


class PropertyUpdate(BaseModel):
    unit_no:   Optional[str]   = None
    floor:     Optional[int]   = None
    type:      Optional[str]   = None
    area_sqft: Optional[float] = None
    owner_id:  Optional[int]   = None


class OwnerMini(BaseModel):
    user_id: int
    name:    str
    mobile:  str
    model_config = {"from_attributes": True}


class PropertyResponse(BaseModel):
    property_id: int
    unit_no:     str
    floor:       int
    type:        str
    area_sqft:   Optional[float]
    owner_id:    Optional[int]
    owner:       Optional[OwnerMini]
    created_at:  datetime
    model_config = {"from_attributes": True}


class PropertyListResponse(BaseModel):
    total: int
    items: list[PropertyResponse]


class OccupantCreate(BaseModel):
    user_id:        int
    occupancy_type: str = "owner"


class OccupantResponse(BaseModel):
    occupant_id:    int
    property_id:    int
    user_id:        int
    occupancy_type: str
    model_config    = {"from_attributes": True}


class DashboardStats(BaseModel):
    total_units:      int
    total_users:      int
    active_users:     int
    bills_paid:       int
    bills_pending:    int
    open_complaints:  int
    unread_notices:   int
    collection_amount: float
    pending_amount:    float

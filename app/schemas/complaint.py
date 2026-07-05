from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ComplaintCreateRequest(BaseModel):
    title:       str
    category:    str
    priority:    str = "medium"
    description: Optional[str] = None


class ComplaintUpdateRequest(BaseModel):
    status:      Optional[str] = None
    assigned_to: Optional[int] = None
    resolution:  Optional[str] = None
    priority:    Optional[str] = None


class ComplaintResponse(BaseModel):
    complaint_id: int
    property_id:  Optional[int]
    raised_by:    Optional[int]
    assigned_to:  Optional[int]
    category:     str
    priority:     str
    status:       str
    title:        str
    description:  Optional[str]
    resolution:   Optional[str]
    created_at:   datetime
    updated_at:   datetime
    unit_no:      Optional[str] = None
    raiser_name:  Optional[str] = None

    model_config = {"from_attributes": True}


class ComplaintListResponse(BaseModel):
    total: int
    items: list[ComplaintResponse]

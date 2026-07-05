from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class NoticeCreateRequest(BaseModel):
    title:    str
    body:     str
    category: Optional[str] = "general"
    priority: str = "normal"


class NoticeUpdateRequest(BaseModel):
    title:     Optional[str] = None
    body:      Optional[str] = None
    category:  Optional[str] = None
    priority:  Optional[str] = None
    is_active: Optional[bool] = None


class NoticeResponse(BaseModel):
    notice_id:   int
    title:       str
    body:        str
    category:    Optional[str]
    priority:    str
    is_active:   bool
    created_by:  Optional[int]
    author_name: Optional[str] = None
    created_at:  datetime

    model_config = {"from_attributes": True}


class NoticeListResponse(BaseModel):
    total: int
    items: list[NoticeResponse]

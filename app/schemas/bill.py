from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import date, datetime


class BillGenerateRequest(BaseModel):
    month:           int
    year:            int
    maintenance:     float
    due_date:        date
    include_penalty: bool = True
    property_id:     Optional[int] = None  # None = all units, int = specific unit

    @field_validator("month")
    @classmethod
    def validate_month(cls, v: int) -> int:
        if not 1 <= v <= 12:
            raise ValueError("Month must be 1–12")
        return v

    @field_validator("maintenance")
    @classmethod
    def validate_maintenance(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Maintenance amount must be positive")
        return v


class BillResponse(BaseModel):
    bill_id:     int
    property_id: int
    unit_no:     Optional[str] = None
    month:       int
    year:        int
    maintenance: float
    penalty:     float
    total:       float
    due_date:    Optional[date]
    status:      str
    created_at:  datetime

    model_config = {"from_attributes": True}


class BillListResponse(BaseModel):
    total: int
    items: List[BillResponse]


class BillSummary(BaseModel):
    """Lightweight summary for dashboard cards."""
    bill_id:    int
    month:      int
    year:       int
    total:      float
    penalty:    float
    status:     str
    due_date:   Optional[date]


class PenaltyPreview(BaseModel):
    """Shows penalty calculation before applying."""
    property_id:     int
    unit_no:         str
    outstanding:     float
    daily_rate_pct:  float
    days_overdue:    int
    penalty_amount:  float
    formula:         str


class GenerationResult(BaseModel):
    generated:    int
    skipped:      int
    total_amount: float
    details:      List[str]

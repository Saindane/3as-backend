from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class PaymentSubmitRequest(BaseModel):
    bill_id:    int
    amount:     float
    utr:        Optional[str] = None
    mode:       str = "upi"
    screenshot: Optional[str] = None   # S3 URL after upload


class PaymentVerifyRequest(BaseModel):
    action: str   # "verify" or "reject"


class PaymentResponse(BaseModel):
    payment_id:  int
    bill_id:     int
    amount:      float
    utr:         Optional[str]
    screenshot:  Optional[str]
    mode:        str
    status:      str
    verified_by: Optional[int]
    verified_at: Optional[datetime]
    created_at:  datetime
    unit_no:     Optional[str] = None

    model_config = {"from_attributes": True}


class PaymentListResponse(BaseModel):
    total: int
    items: list[PaymentResponse]

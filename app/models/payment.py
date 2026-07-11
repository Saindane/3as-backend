import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Enum, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base


class PaymentMode(str, enum.Enum):
    UPI     = "UPI"
    NEFT    = "NEFT"
    RTGS    = "RTGS"
    CASH    = "CASH"
    CHEQUE  = "CHEQUE"


class PaymentStatus(str, enum.Enum):
    PENDING  = "PENDING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"


class Payment(Base):
    __tablename__ = "payments"

    payment_id   = Column(Integer, primary_key=True, index=True)
    bill_id      = Column(Integer, ForeignKey("bills.bill_id", ondelete="CASCADE"))
    amount       = Column(Float,   nullable=False)
    utr          = Column(String(100), nullable=True)
    screenshot   = Column(String(500), nullable=True)   # S3 URL
    mode         = Column(Enum(PaymentMode), nullable=False, default=PaymentMode.UPI)
    status       = Column(Enum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING)
    verified_by  = Column(Integer, ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    verified_at  = Column(DateTime(timezone=True), nullable=True)
    created_at   = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    bill         = relationship("Bill", back_populates="payments")
    verifier     = relationship("User", foreign_keys=[verified_by], lazy="joined")

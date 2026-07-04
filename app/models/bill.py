import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Enum, DateTime, ForeignKey, Date
from sqlalchemy.orm import relationship
from app.db.base import Base


class BillStatus(str, enum.Enum):
    PENDING  = "PENDING"
    PAID     = "PAID"
    OVERDUE  = "OVERDUE"
    WAIVED   = "WAIVED"


class Bill(Base):
    __tablename__ = "bills"

    bill_id     = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.property_id", ondelete="CASCADE"))
    month       = Column(Integer, nullable=False)   # 1-12
    year        = Column(Integer, nullable=False)
    maintenance = Column(Float,   nullable=False, default=0.0)
    penalty     = Column(Float,   nullable=False, default=0.0)
    total       = Column(Float,   nullable=False, default=0.0)
    due_date    = Column(Date,    nullable=True)
    status      = Column(Enum(BillStatus), nullable=False, default=BillStatus.PENDING)
    created_at  = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at  = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                         onupdate=lambda: datetime.now(timezone.utc))

    property = relationship("Property", lazy="joined")
    payments = relationship("Payment", back_populates="bill", lazy="select")

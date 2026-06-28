import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Enum, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base


class ComplaintCategory(str, enum.Enum):
    ELECTRICAL   = "electrical"
    PLUMBING     = "plumbing"
    CIVIL        = "civil"
    SECURITY     = "security"
    HOUSEKEEPING = "housekeeping"
    COMMON_AREA  = "common_area"
    OTHER        = "other"


class ComplaintPriority(str, enum.Enum):
    LOW    = "low"
    MEDIUM = "medium"
    HIGH   = "high"


class ComplaintStatus(str, enum.Enum):
    NEW         = "new"
    ASSIGNED    = "assigned"
    IN_PROGRESS = "in_progress"
    RESOLVED    = "resolved"
    CLOSED      = "closed"


class Complaint(Base):
    __tablename__ = "complaints"

    complaint_id = Column(Integer, primary_key=True, index=True)
    property_id  = Column(Integer, ForeignKey("properties.property_id", ondelete="SET NULL"), nullable=True)
    raised_by    = Column(Integer, ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    assigned_to  = Column(Integer, ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    category     = Column(Enum(ComplaintCategory), nullable=False)
    priority     = Column(Enum(ComplaintPriority), nullable=False, default=ComplaintPriority.MEDIUM)
    status       = Column(Enum(ComplaintStatus),   nullable=False, default=ComplaintStatus.NEW)
    title        = Column(String(200), nullable=False)
    description  = Column(Text, nullable=True)
    resolution   = Column(Text, nullable=True)
    created_at   = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at   = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                          onupdate=lambda: datetime.now(timezone.utc))

    property   = relationship("Property", foreign_keys=[property_id], lazy="joined")
    raiser     = relationship("User", foreign_keys=[raised_by],  lazy="joined")
    assignee   = relationship("User", foreign_keys=[assigned_to], lazy="joined")

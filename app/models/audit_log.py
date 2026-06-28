from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from app.db.base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    log_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    action = Column(String(100), nullable=False)       # e.g. "LOGIN", "BILL_GENERATED"
    entity = Column(String(50), nullable=True)         # e.g. "User", "Bill"
    entity_id = Column(Integer, nullable=True)
    detail = Column(Text, nullable=True)               # JSON string for extra context
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

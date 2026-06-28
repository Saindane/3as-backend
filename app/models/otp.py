from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from app.db.base import Base


class OTPRecord(Base):
    __tablename__ = "otp_records"

    id = Column(Integer, primary_key=True, index=True)
    mobile = Column(String(15), nullable=False, index=True)
    otp_hash = Column(String(255), nullable=False)     # bcrypt hashed OTP
    purpose = Column(String(30), nullable=False)        # "password_reset" | "login"
    is_used = Column(Boolean, default=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

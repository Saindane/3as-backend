import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, Enum, DateTime
from app.db.base import Base


class UserRole(str, enum.Enum):
    RESIDENT   = "RESIDENT"
    MANAGEMENT = "MANAGEMENT"
    ADMIN      = "ADMIN"


class User(Base):
    __tablename__ = "users"

    user_id       = Column(Integer, primary_key=True, index=True)
    name          = Column(String(100), nullable=False)
    mobile        = Column(String(15), unique=True, nullable=False, index=True)
    email         = Column(String(150), unique=True, nullable=True)
    password_hash = Column(String(255), nullable=False)
    role          = Column(Enum(UserRole), nullable=False, default=UserRole.RESIDENT)
    is_active     = Column(Boolean, default=True, nullable=False)
    fcm_token     = Column(String(255), nullable=True)
    created_at    = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at    = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self):
        return f"<User {self.user_id} {self.mobile} [{self.role}]>"

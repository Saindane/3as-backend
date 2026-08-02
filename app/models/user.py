import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime
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
    # Use String instead of Enum — avoids SQLAlchemy/PostgreSQL enum mismatch
    role          = Column(String(20), nullable=False, default="RESIDENT")
    is_active              = Column(Boolean, default=True,  nullable=False)
    must_change_password   = Column(Boolean, default=False, nullable=False)
    fcm_token     = Column(String(255), nullable=True)
    created_at    = Column(DateTime(timezone=True),
                           default=lambda: datetime.now(timezone.utc))
    updated_at    = Column(DateTime(timezone=True),
                           default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    @property
    def role_enum(self) -> UserRole:
        """Return role as enum — handles both upper and lowercase DB values."""
        try:
            return UserRole(self.role.upper())
        except ValueError:
            return UserRole.RESIDENT

    def __repr__(self):
        return f"<User {self.user_id} {self.mobile} [{self.role}]>"

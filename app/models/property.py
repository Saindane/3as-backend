import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Enum, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base


class PropertyType(str, enum.Enum):
    RESIDENTIAL = "RESIDENTIAL"
    COMMERCIAL  = "COMMERCIAL"


class OccupancyType(str, enum.Enum):
    OWNER  = "OWNER"
    TENANT = "TENANT"


class Property(Base):
    __tablename__ = "properties"

    property_id = Column(Integer, primary_key=True, index=True)
    unit_no     = Column(String(20),  nullable=False, unique=True)
    floor       = Column(Integer,     nullable=False)
    type        = Column(Enum(PropertyType), nullable=False, default=PropertyType.RESIDENTIAL)
    area_sqft   = Column(Float,       nullable=True)
    owner_id    = Column(Integer, ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    created_at  = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at  = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                         onupdate=lambda: datetime.now(timezone.utc))

    owner       = relationship("User", foreign_keys=[owner_id], lazy="joined")
    occupants   = relationship("Occupant", back_populates="property", lazy="select")


class Occupant(Base):
    __tablename__ = "occupants"

    occupant_id    = Column(Integer, primary_key=True, index=True)
    property_id    = Column(Integer, ForeignKey("properties.property_id", ondelete="CASCADE"))
    user_id        = Column(Integer, ForeignKey("users.user_id",     ondelete="CASCADE"))
    occupancy_type = Column(Enum(OccupancyType), nullable=False, default=OccupancyType.OWNER)
    created_at     = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    property = relationship("Property", back_populates="occupants")
    user     = relationship("User", foreign_keys=[user_id], lazy="joined")

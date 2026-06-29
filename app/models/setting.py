from sqlalchemy import Column, String
from app.db.base import Base


class Setting(Base):
    __tablename__ = "settings"

    key   = Column(String(100), primary_key=True)
    value = Column(String(500), nullable=False)

    def __repr__(self):
        return f"<Setting {self.key}={self.value}>"

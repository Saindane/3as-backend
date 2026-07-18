from sqlalchemy import Column, String, Text
from app.db.base import Base


class Setting(Base):
    __tablename__ = "settings"

    key   = Column(String(100), primary_key=True)
    value = Column(Text, nullable=False)

    def __repr__(self):
        return f"<Setting {self.key}={self.value}>"

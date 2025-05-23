
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum, JSON, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.db.base import Base


class ChangeType(str, enum.Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    SHARE = "share"
    PERMISSION_CHANGE = "permission_change"
    ROLLBACK = "rollback"


class ChangeLog(Base):
    __tablename__ = "changelog"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    change_type = Column(Enum(ChangeType), nullable=False)
    from_version = Column(Integer, nullable=True)
    to_version = Column(Integer, nullable=True)
    changes = Column(JSON, nullable=True)  
    comment = Column(Text, nullable=True)

    
    event = relationship("Event", back_populates="changelog")
    user = relationship("User", back_populates="event_changes")
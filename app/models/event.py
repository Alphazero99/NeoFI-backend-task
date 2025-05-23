# File: app/models/event.py
from sqlalchemy import Boolean, Column, Integer, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import Base


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    description = Column(Text)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    location = Column(String)
    is_recurring = Column(Boolean, default=False)
    recurrence_pattern = Column(JSON, nullable=True)  # Store recurrence rules as JSON
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    current_version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    owner = relationship("User", back_populates="events")
    permissions = relationship("Permission", back_populates="event", cascade="all, delete-orphan")
    versions = relationship("EventVersion", back_populates="event", cascade="all, delete-orphan")
    changelog = relationship("ChangeLog", back_populates="event", cascade="all, delete-orphan")


class EventVersion(Base):
    __tablename__ = "event_versions"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    location = Column(String)
    is_recurring = Column(Boolean, default=False)
    recurrence_pattern = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Relationships
    event = relationship("Event", back_populates="versions")
    created_by = relationship("User")

    class Config:
        unique_together = ("event_id", "version_number")
# File: app/schemas/event.py
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, validator
from datetime import datetime


# Recurrence pattern schema
class RecurrencePattern(BaseModel):
    frequency: str  # daily, weekly, monthly, yearly
    interval: int = 1  # every n days, weeks, etc.
    count: Optional[int] = None  # number of occurrences
    until: Optional[datetime] = None  # end date
    weekdays: Optional[List[int]] = None  # 0-6 for Monday-Sunday
    monthdays: Optional[List[int]] = None  # 1-31 for days of month
    months: Optional[List[int]] = None  # 1-12 for months


# Base Event Schema
class EventBase(BaseModel):
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    location: Optional[str] = None
    is_recurring: bool = False
    recurrence_pattern: Optional[RecurrencePattern] = None

    @validator("end_time")
    def end_time_must_be_after_start_time(cls, v, values):
        if "start_time" in values and v < values["start_time"]:
            raise ValueError("end_time must be after start_time")
        return v


# Create Event Schema
class EventCreate(EventBase):
    pass


# Update Event Schema
class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    location: Optional[str] = None
    is_recurring: Optional[bool] = None
    recurrence_pattern: Optional[RecurrencePattern] = None


# Event in DB Schema
class EventInDBBase(EventBase):
    id: int
    owner_id: int
    current_version: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


# Event Schema for responses
class Event(EventInDBBase):
    pass


# Event Version Schema
class EventVersion(BaseModel):
    version_number: int
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    location: Optional[str] = None
    is_recurring: bool
    recurrence_pattern: Optional[RecurrencePattern] = None
    created_at: datetime
    created_by_id: int

    class Config:
        orm_mode = True


# Batch Event Creation
class BatchEventCreate(BaseModel):
    events: List[EventCreate]


# Event Filter Query Parameters
class EventFilterParams(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    title_search: Optional[str] = None
    location: Optional[str] = None
    include_recurring: bool = True


# Pagination
class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    page_size: int
    pages: int


# Event List Response
class EventListResponse(PaginatedResponse):
    items: List[Event]
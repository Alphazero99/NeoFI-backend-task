
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, validator
from datetime import datetime



class RecurrencePattern(BaseModel):
    frequency: str  
    interval: int = 1  
    count: Optional[int] = None  
    until: Optional[datetime] = None  
    weekdays: Optional[List[int]] = None  
    monthdays: Optional[List[int]] = None  
    months: Optional[List[int]] = None  



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



class EventCreate(EventBase):
    pass



class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    location: Optional[str] = None
    is_recurring: Optional[bool] = None
    recurrence_pattern: Optional[RecurrencePattern] = None



class EventInDBBase(EventBase):
    id: int
    owner_id: int
    current_version: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True



class Event(EventInDBBase):
    pass



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



class BatchEventCreate(BaseModel):
    events: List[EventCreate]


class EventFilterParams(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    title_search: Optional[str] = None
    location: Optional[str] = None
    include_recurring: bool = True



class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    page_size: int
    pages: int



class EventListResponse(PaginatedResponse):
    items: List[Event]
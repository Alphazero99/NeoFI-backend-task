# File: app/schemas/changelog.py
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from datetime import datetime

from app.models.changelog import ChangeType


# Base Changelog Schema
class ChangeLogBase(BaseModel):
    change_type: ChangeType
    from_version: Optional[int] = None
    to_version: Optional[int] = None
    changes: Optional[Dict[str, Any]] = None
    comment: Optional[str] = None


# Changelog in DB Schema
class ChangeLogInDBBase(ChangeLogBase):
    id: int
    event_id: int
    user_id: int
    timestamp: datetime

    class Config:
        orm_mode = True


# Changelog Schema for responses
class ChangeLog(ChangeLogInDBBase):
    pass


# Changelog List response
class ChangeLogList(BaseModel):
    event_id: int
    changes: List[ChangeLog]


# Field Change
class FieldChange(BaseModel):
    field: str
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None


# Diff Response
class DiffResponse(BaseModel):
    event_id: int
    version1: int
    version2: int
    changes: List[FieldChange]


# Rollback Request
class RollbackRequest(BaseModel):
    comment: Optional[str] = None
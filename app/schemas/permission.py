# File: app/schemas/permission.py
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.models.permission import RoleType


# Base Permission Schema
class PermissionBase(BaseModel):
    role: RoleType


# Create Permission Schema
class PermissionCreate(PermissionBase):
    user_id: int
    event_id: int


# Update Permission Schema
class PermissionUpdate(BaseModel):
    role: RoleType


# Permission in DB Schema
class PermissionInDBBase(PermissionBase):
    id: int
    event_id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


# Permission Schema for responses
class Permission(PermissionInDBBase):
    pass


# Share Event Request
class ShareEventRequest(BaseModel):
    users: List[PermissionCreate]


# User Permission Info
class UserPermissionInfo(BaseModel):
    user_id: int
    username: str
    email: str
    role: RoleType


# Event Permissions List
class EventPermissionsList(BaseModel):
    event_id: int
    permissions: List[UserPermissionInfo]
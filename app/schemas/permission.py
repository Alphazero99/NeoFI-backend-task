
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.models.permission import RoleType



class PermissionBase(BaseModel):
    role: RoleType



class PermissionCreate(PermissionBase):
    user_id: int
    event_id: int



class PermissionUpdate(BaseModel):
    role: RoleType



class PermissionInDBBase(PermissionBase):
    id: int
    event_id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True



class Permission(PermissionInDBBase):
    pass



class ShareEventRequest(BaseModel):
    users: List[PermissionCreate]



class UserPermissionInfo(BaseModel):
    user_id: int
    username: str
    email: str
    role: RoleType



class EventPermissionsList(BaseModel):
    event_id: int
    permissions: List[UserPermissionInfo]
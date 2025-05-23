
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from datetime import datetime

from app.models.changelog import ChangeType



class ChangeLogBase(BaseModel):
    change_type: ChangeType
    from_version: Optional[int] = None
    to_version: Optional[int] = None
    changes: Optional[Dict[str, Any]] = None
    comment: Optional[str] = None



class ChangeLogInDBBase(ChangeLogBase):
    id: int
    event_id: int
    user_id: int
    timestamp: datetime

    class Config:
        orm_mode = True



class ChangeLog(ChangeLogInDBBase):
    pass



class ChangeLogList(BaseModel):
    event_id: int
    changes: List[ChangeLog]



class FieldChange(BaseModel):
    field: str
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None



class DiffResponse(BaseModel):
    event_id: int
    version1: int
    version2: int
    changes: List[FieldChange]



class RollbackRequest(BaseModel):
    comment: Optional[str] = None
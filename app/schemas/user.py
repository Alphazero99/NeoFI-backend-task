
from typing import Optional, List, ClassVar, Dict, Any
from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime



class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool = True



class UserCreate(UserBase):
    password: str

    @field_validator("password")
    def password_min_length(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v



class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None



class UserInDBBase(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}



class User(UserInDBBase):
    pass



class UserInDB(UserInDBBase):
    hashed_password: str



class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str
    exp: int
    type: str



class UserLogin(BaseModel):
    username: str
    password: str



class RefreshToken(BaseModel):
    refresh_token: str
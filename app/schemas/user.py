# File: app/schemas/user.py
from typing import Optional, List, ClassVar, Dict, Any
from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime


# Shared properties
class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool = True


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str

    @field_validator("password")
    def password_min_length(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v


# Properties to receive via API on update
class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None


# Properties shared by models stored in DB
class UserInDBBase(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# Properties to return to client
class User(UserInDBBase):
    pass


# Properties stored in DB
class UserInDB(UserInDBBase):
    hashed_password: str


# Token data
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str
    exp: int
    type: str


# Login data
class UserLogin(BaseModel):
    username: str
    password: str


# Refresh token
class RefreshToken(BaseModel):
    refresh_token: str
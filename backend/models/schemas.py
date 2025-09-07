from pydantic import BaseModel, EmailStr
from typing import Optional

class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool
    kakao_id: Optional[str] = None
    google_id: Optional[str] = None
    naver_id: Optional[str] = None

    class Config:
        from_attributes = True # For Pydantic v2

from datetime import datetime

class ActivityLogBase(BaseModel):
    activity_type: str
    description: str

class ActivityLogCreate(ActivityLogBase):
    user_id: Optional[int] = None

class ActivityLog(ActivityLogBase):
    id: int
    user_id: Optional[int] = None
    timestamp: datetime

    class Config:
        from_attributes = True

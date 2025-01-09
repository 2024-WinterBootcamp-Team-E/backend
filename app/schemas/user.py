from typing import Optional
from pydantic import BaseModel
from datetime import datetime
from app.schemas.feedback import Feedback

class UserWithFeedback(BaseModel):
    user_id: int
    email: str
    nickname: str
    created_at: datetime
    updated_at: datetime
    is_deleted: bool
    feedbacks: Optional[list[Feedback]]

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    nickname: str
    # 값 추가 입력
    class Config:
        from_attributes = True

class UserCreate(BaseModel):
    email: str
    password: str
    nickname: str

class UserLogin(BaseModel):
    email: str
    password: str



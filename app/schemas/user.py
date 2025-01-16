from typing import Optional
from pydantic import BaseModel
from app.schemas.feedback import Feedback
class UserWithFeedback(BaseModel):
    user_id: int
    email: str
    nickname: str
    feedbacks: Optional[list[Feedback]]
    class Config:
        from_attributes = True
class UserUpdate(BaseModel):
    nickname: str
    class Config:
        from_attributes = True
class UserCreate(BaseModel):
    email: str
    password: str
    nickname: str
class UserLogin(BaseModel):
    email: str
    password: str



from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.schemas.feedback import Feedback

class UserWithFeedback(BaseModel): #user 테이블 정보 + 피드백 list
    user_id: int
    email: str
    nickname: str
    created_at: datetime
    updated_at: datetime
    is_deleted: bool
    feedbacks: Optional[list[Feedback]]

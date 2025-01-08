from typing import Optional

from pydantic import BaseModel
from datetime import datetime

class UserResponse(BaseModel):
    user_id: int
    id: str
    nickname: str
    created_at: datetime
    modified_at: datetime
    is_deleted: bool


class UserUpdate(BaseModel):
    nickname: str
    # 값 추가 입력
    class Config:
        orm_mode = True

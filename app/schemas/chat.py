from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ChatResponse(BaseModel):
    chat_id: int
    user_id: int
    character_id: int
    score: Optional[int] = None  # None 값을 허용
    subject: str
    created_at: datetime
    updated_at: datetime
    is_deleted: bool
    class Config:
        from_attributes = True


class ChatRoomCreateRequest(BaseModel):
    character_name: str
    subject: str

class Chatroomresponse(BaseModel):
    score: int
    subject: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ChatRoomCreateRequest(BaseModel):
    character_name: str
    subject: str

class Chatroomresponse(BaseModel):
    chat_id:int
    user_id: int
    score: Optional[int]
    subject: str
    character_name: str
    tts_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
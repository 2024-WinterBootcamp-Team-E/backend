from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ChatRoomCreateRequest(BaseModel):
    character_name: str
    title: str

class Chatroomresponse(BaseModel):
    chat_id:int
    user_id: int
    score: Optional[int]
    title: str
    character_name: str
    tts_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
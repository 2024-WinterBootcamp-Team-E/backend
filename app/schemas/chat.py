from pydantic import BaseModel
from datetime import datetime

class ChatRoomCreateRequest(BaseModel):
    character_name: str
    title: str

class Chatroomresponse(BaseModel):
    chat_id:int
    title: str
    character_name: str
    updated_at: datetime
    class Config:
        from_attributes = True
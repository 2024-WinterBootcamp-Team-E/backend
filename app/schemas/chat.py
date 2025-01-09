from pydantic import BaseModel
from datetime import datetime

class ChatResponse(BaseModel):
    chat_id: int
    user_id: int
    character_id : int
    score : int
    situation : str
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    class Config:
        from_attributes = True

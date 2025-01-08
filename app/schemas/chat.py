from pydantic import BaseModel
from datetime import datetime

class ChatResponse(BaseModel):
    chat_id: int
    user_id: str
    character_id : int
    score : int
    situation : str
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

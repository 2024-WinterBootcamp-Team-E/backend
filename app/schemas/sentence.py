from pydantic import BaseModel
from datetime import datetime
from typing import List
class Sentence(BaseModel):
    sentence_id: int
    situation: str
    created_at: datetime
    updated_at: datetime
    is_deleted: bool
    content: str
    voice_url: str
    class Config:
        from_attributes = True

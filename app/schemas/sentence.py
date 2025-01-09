from pydantic import BaseModel
from datetime import datetime

class Sentence(BaseModel):
    sentence_id: int
    content: str
    situation: str
    voice_url : str
    created_at: datetime
    updated_at: datetime
    is_deleted : bool

    class Config:
        from_attributes = True
from pydantic import BaseModel
from app.schemas.sentence import Sentence
from datetime import datetime

class Feedback(BaseModel):
    feedback_id: int
    sentence: Sentence
    user_id: int
    sentence_id: int
    accuracy: float
    content: str
    pronunciation_feedback: str
    created_at: datetime
    updated_at: datetime
    deleted_at: bool

    class Config:
        from_attributes = True
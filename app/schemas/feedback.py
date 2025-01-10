from pydantic import BaseModel
from app.schemas.sentence import Sentence
from datetime import datetime
class Feedback(BaseModel):
    feedback_id: int
    user_id: int
    sentence_id: str
    accuracy: float
    content: str
    pronunciation_feedback: str
    created_at: datetime
    updated_at: datetime
    is_deleted: bool
    class Config:
        from_attributes = True
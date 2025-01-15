from pydantic import BaseModel
from app.schemas.sentence import Sentence
from datetime import datetime

class Feedback(BaseModel):
    feedback_id: int
    user_id: int
    sentence: Sentence
    pronunciation_feedback: str
    class Config:
        from_attributes = True

class PronunciationResultResponse(BaseModel):
    accuracy: float
    feedback: str
    content: str
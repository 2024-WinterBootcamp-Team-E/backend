from pydantic import BaseModel
from app.schemas.sentence import Sentence

class Feedback(BaseModel):
    feedback_id: int
    sentence: Sentence
    accuracy: float
    content: str
    feedback: str

    class Config:
        from_attributes = True
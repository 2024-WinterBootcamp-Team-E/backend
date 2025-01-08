from pydantic import BaseModel

class Feedback(BaseModel):
    feedback_id: int
    sentence_id: int
    content: str
    feedback: str

    class Config:
        from_attributes = True  # Pydantic v2에서 필요한 설정
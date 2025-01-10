from pydantic import BaseModel
from app.models.sentence import SituationType
class Sentence(BaseModel):
    sentence_id: int
    situation: SituationType
    content: str
    voice_url: str
    class Config:
        from_attributes = True

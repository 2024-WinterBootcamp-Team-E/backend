from pydantic import BaseModel

class Sentence(BaseModel):
    sentence_id: int
    content: str
    situation: str
    voice_url: str

    class Config:
        from_attributes = True
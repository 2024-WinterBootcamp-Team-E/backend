from pydantic import BaseModel
class CharacterResponse(BaseModel):
    character_id: int
    name: str
    description: str
    image_url: str
    class Config:
        from_attributes = True

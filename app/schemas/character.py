from pydantic import BaseModel
from datetime import datetime

class ChatResponse(BaseModel):
    character_id : int
    name : str
    description : str
    created_at: datetime
    modified_at: datetime

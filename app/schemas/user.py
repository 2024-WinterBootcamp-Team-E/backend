from pydantic import BaseModel
from datetime import datetime

class UserResponse(BaseModel):
    user_id: int
    id: str
    nickname: str
    created_at: datetime
    modified_at: datetime
    is_deleted: bool
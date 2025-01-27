from pydantic import BaseModel
from datetime import datetime
from app.schemas.feedback import Feedback
from app.schemas.chat import Chatroomresponse

class DailyFeedback(BaseModel):
    user_id: int
    selected_day: datetime
    feedbacks_count: int
    chatrooms_count: int
    total_count: int
    feedbacks: list[Feedback]
    chatrooms: list[Chatroomresponse]
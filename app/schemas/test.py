from pydantic import BaseModel
from datetime import datetime
from app.schemas.feedback import Feedback
from app.schemas.chat import Chatroomresponse


class DailyFeedback(BaseModel):
    user_id: int
    selected_day: datetime
    feedbacks_count: int  # 필수 필드로 설정
    chatrooms_count: int  # 필수 필드로 설정
    total_count: int  # 필수 필드로 설정
    feedbacks: list[Feedback]
    chatrooms: list[Chatroomresponse]
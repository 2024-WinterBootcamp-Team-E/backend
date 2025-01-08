from pydantic import BaseModel
from datetime import datetime

class FeedbackResponse(BaseModel):
    feedback_id: int
    user_id: int
    sentence_id : int
    accuracy : float
    content : str
    pronunciation_feedback : str
    created_at: datetime
    updated_at: datetime
    deleted_at : bool

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status
from app.models import Feedback
from app.models.chat import Chat
from app.schemas.test import DailyFeedback
from app.schemas.feedback import Feedback as FeedbackSchema
from app.schemas.chat import Chatroomresponse as ChatSchema
from datetime import datetime, timedelta

def dailytask(db: Session, user_id: int, selected_day: datetime):
    try:
        day_start = selected_day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1) - timedelta(microseconds=1)
        feedbacks = (
            db.query(Feedback)
            .filter(Feedback.user_id == user_id)
            .filter(Feedback.updated_at >= day_start)
            .filter(Feedback.updated_at <= day_end)
            .all()
        )
        chatrooms = (
            db.query(Chat)
            .filter(Chat.user_id == user_id)
            .filter(Chat.updated_at >= day_start)
            .filter(Chat.updated_at <= day_end)
            .all()
        )
        feedbacks_as_schemas = [FeedbackSchema.model_validate(feedback) for feedback in feedbacks]
        chatrooms_as_schemas = [ChatSchema.model_validate(chatroom) for chatroom in chatrooms]
        feedbacks_count = len(feedbacks_as_schemas)
        chatrooms_count = len(chatrooms_as_schemas)
        total_count = feedbacks_count + chatrooms_count

        daily_tasks = DailyFeedback(
            user_id=user_id,
            selected_day=selected_day,
            feedbacks_count=feedbacks_count,
            chatrooms_count=chatrooms_count,
            total_count=total_count,
            feedbacks=feedbacks_as_schemas,
            chatrooms=chatrooms_as_schemas,
        )
        return daily_tasks
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )

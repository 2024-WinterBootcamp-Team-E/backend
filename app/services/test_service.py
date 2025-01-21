from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status
from app.models import Feedback
from app.models.chat import Chat
from app.schemas.test import DailyFeedback
from app.schemas.feedback import Feedback as FeedbackSchema
from app.schemas.chat import Chatroomresponse as ChatSchema
from datetime import datetime, timedelta

# user_id와 원하는 날짜 selected_day 값을 매개변수로 받도록 수정
# feedback과 chat의 데이터를 모두 정리하고, feedback 개수, chat 개수, total 개수도 응답에 포함
def dailytask(db: Session, user_id: int, selected_day: datetime):
    try:
        # 선택한 날짜의 시작과 끝 계산
        day_start = selected_day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1) - timedelta(microseconds=1)

        # Feedback 데이터 필터링
        feedbacks = (
            db.query(Feedback)
            .filter(Feedback.user_id == user_id)
            .filter(Feedback.updated_at >= day_start)
            .filter(Feedback.updated_at <= day_end)
            .all()
        )

        # Chat 데이터 필터링
        chatrooms = (
            db.query(Chat)
            .filter(Chat.user_id == user_id)
            .filter(Chat.updated_at >= day_start)
            .filter(Chat.updated_at <= day_end)
            .all()
        )

        # SQLAlchemy 객체를 Pydantic 모델로 변환
        feedbacks_as_schemas = [FeedbackSchema.model_validate(feedback) for feedback in feedbacks]
        chatrooms_as_schemas = [ChatSchema.model_validate(chatroom) for chatroom in chatrooms]

        # 개수 계산
        feedbacks_count = len(feedbacks_as_schemas)
        chatrooms_count = len(chatrooms_as_schemas)
        total_count = feedbacks_count + chatrooms_count

        # DailyFeedback 객체 생성
        daily_tasks = DailyFeedback(
            user_id=user_id,
            updated_at=datetime.now(),
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

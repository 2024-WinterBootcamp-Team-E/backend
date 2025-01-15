from sqlalchemy.orm import Session, joinedload
from app.models.feedback import Feedback
from app.schemas.user import UserWithFeedback
from app.models.user import User
from app.config.azure.pronunciation_feedback import analyze_pronunciation_with_azure
from fastapi import HTTPException
from app.config.openAI.openai_service import get_pronunciation_feedback

def get_feedbacks(user: User, db: Session):
    feedbacks = db.query(Feedback).options(
        joinedload(Feedback.sentence)
    ).filter(
        Feedback.user_id == user.user_id,
    ).all()
    user_with_feedback = UserWithFeedback(
        user_id=user.user_id,
        email=user.email,
        nickname=user.nickname,
        feedbacks=feedbacks
    )
    return user_with_feedback

async def create_feedback_from_azure_response(
    user_id: int,
    sentence_id: int,
    azure_response: str, # str로 변경해야됨
    db: Session
):
    feedback = Feedback(
        user_id=user_id,
        sentence_id=sentence_id,
        accuracy=azure_response.get("pronunciation_score", 'N/A'),
        content=azure_response.get("text", ""),
        pronunciation_feedback=(
            f"Fluency: {azure_response.get('fluency_score', 'N/A')}, "
            f"Completeness: {azure_response.get('completeness_score', 'N/A')}, "
            f"Pronunciation: {azure_response.get('pronunciation_score', 'N/A')}"
        ),
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback
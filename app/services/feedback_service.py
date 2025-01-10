from sqlalchemy.orm import Session, joinedload
from app.models.feedback import Feedback
from app.schemas.user import UserWithFeedback
from app.models.user import User

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
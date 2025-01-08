from sqlalchemy.orm import Session
from app.models.feedback import Feedback

def get_feedbacks(user_id: int, db: Session):
    feedbacks = db.query(Feedback).filter(
        Feedback.user_id == user_id,
    ).all()
    return feedbacks
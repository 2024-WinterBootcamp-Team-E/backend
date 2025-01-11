from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.sentence import Sentence, SituationType
from app.models.feedback import Feedback

def get_situation_type():
    return [situation.value for situation in SituationType]

situation_mapping = {
    "여행": "TRAVEL",
    "비즈니스": "BUSINESS",
    "일상": "DAILY",
    "영화": "MOVIE"
}

def get_sentences_by_situation(situation: str, db: Session):
    try:
        if situation in [s.value for s in SituationType]:
            situation_enum = next(s for s in SituationType if s.value == situation)
        else:
            situation_enum = SituationType[situation]
    except (KeyError, StopIteration):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid situation!. Valid values are: {[s.value for s in SituationType]}"
        )
    return db.query(Sentence).filter_by(situation=situation_enum.name).all()

def get_pronunciation_feedback(user_id: int, sentence_id: int, db: Session):
    feedback = db.query(Feedback).filter(
        Feedback.user_id == user_id,
        Feedback.sentence_id == sentence_id,
        Feedback.is_deleted == False
    ).first()
    return feedback
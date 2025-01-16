from typing import Optional, Dict
from sqlalchemy import desc, func
from sqlalchemy.orm import Session, joinedload
from app.models.feedback import Feedback
from app.schemas.user import UserWithFeedback
from app.models.user import User
import json
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
    azure_response: str,
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
            f""
        ),
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)


def get_value(key, json_string):
    try:
        json_data = json.loads(json_string)  # JSON 변환
        pronunciation_assessment = json_data.get("NBest", [{}])[0].get("PronunciationAssessment", {})
        value = pronunciation_assessment.get(key)
        if value is None:
            raise ValueError(f"키 {key}를 찾을 수 없습니다.")
        return float(value)  # 값을 실수로 변환
    except json.JSONDecodeError as e:
        print(f"[ERROR] JSON decoding failed: {e}")
        raise ValueError("JsonResult가 올바른 JSON 형식이 아닙니다.")
    except ValueError as e:
        print(f"[ERROR] {e}")
        raise
    return feedback

def get_avg_score(user_id: int, db: Session) -> Dict[str, Optional[float]]:
    # 서브쿼리를 사용하여 최신 10개의 피드백을 가져옵니다.
    latest_feedbacks_subquery = (
        db.query(Feedback)
        .filter(Feedback.user_id == user_id)
        .order_by(desc(Feedback.updated_at))
        .limit(10)
        .subquery()
    )

    # 서브쿼리에서 각 점수의 평균을 계산합니다.
    averages = db.query(
        func.avg(latest_feedbacks_subquery.c.accuracy_score).label('average_accuracy'),
        func.avg(latest_feedbacks_subquery.c.fluency_score).label('average_fluency'),
        func.avg(latest_feedbacks_subquery.c.completeness_score).label('average_completeness'),
        func.avg(latest_feedbacks_subquery.c.pron_score).label('average_pron')
    ).one()

    # 결과를 딕셔너리로 반환합니다. 평균이 없을 경우 None을 반환할 수 있습니다.
    return {
        "average_accuracy_score": round(averages.average_accuracy, 1) if averages.average_accuracy is not None else None,
        "average_fluency_score": round(averages.average_fluency, 1) if averages.average_fluency is not None else None,
        "average_completeness_score": round(averages.average_completeness, 1) if averages.average_completeness is not None else None,
        "average_pron_score": round(averages.average_pron, 1) if averages.average_pron is not None else None
    }
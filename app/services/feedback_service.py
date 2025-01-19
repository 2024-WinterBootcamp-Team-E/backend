from typing import Optional, Dict
from sqlalchemy import desc, func, cast, Date
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
    # 피드백을 날짜별로 그룹화하기 위해 updated_at을 날짜로 변환
    daily_feedbacks = (
        db.query(
            cast(Feedback.updated_at, Date).label('date'),
            Feedback.accuracy_score,
            Feedback.fluency_score,
            Feedback.completeness_score,
            Feedback.pron_score
        )
        .filter(Feedback.user_id == user_id)
        .subquery()
    )

    # 서브쿼리에서 각 점수의 평균을 계산합니다.
    daily_averages = (
        db.query(
            daily_feedbacks.c.date,
            func.avg(daily_feedbacks.c.accuracy_score).label('average_accuracy'),
            func.avg(daily_feedbacks.c.fluency_score).label('average_fluency'),
            func.avg(daily_feedbacks.c.completeness_score).label('average_completeness'),
            func.avg(daily_feedbacks.c.pron_score).label('average_pron')
        )
        .group_by(daily_feedbacks.c.date)
        .order_by(desc(daily_feedbacks.c.date))
        .limit(10)
        .all()
    )

    # 결과를 리스트 형태로 변환
    result = []
    for avg in daily_averages:
        result.append({
            "date": avg.date.isoformat(),
            "average_accuracy_score": round(avg.average_accuracy, 1) if avg.average_accuracy is not None else None,
            "average_fluency_score": round(avg.average_fluency, 1) if avg.average_fluency is not None else None,
            "average_completeness_score": round(avg.average_completeness, 1) if avg.average_completeness is not None else None,
            "average_pron_score": round(avg.average_pron, 1) if avg.average_pron is not None else None
        })

    return result
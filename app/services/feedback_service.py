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
from motor.motor_asyncio import AsyncIOMotorDatabase
import asyncio

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

async def extract_weak_pronunciations(processed_words, user_id: int, mdb:AsyncIOMotorDatabase, threshold):
    try:
        # 1) 약한 음절을 담을 리스트 (디버깅, 로깅 용도)
        weak_syllables = []

        # 2) 전처리된 words를 순회
        for word_data in processed_words:
            word = word_data.get("Word", "")

            # 3) 각 단어의 Syllables 데이터 확인
            syllables = word_data.get("Syllables", [])
            for syllable_data in syllables:
                syllable = syllable_data.get("Syllable", "")
                pron_assessment = syllable_data.get("PronunciationAssessment", {})
                accuracy_score = pron_assessment.get("AccuracyScore", 100.0)

                # 4) 정확도 점수가 임계값 이하일 경우 약한 발음으로 처리
                if accuracy_score <= threshold:
                    weak_syllables.append({
                        "word": word,
                        "syllable": syllable,
                        "accuracy_score": accuracy_score
                    })

                    # 5) MongoDB에 약점(syllable) 데이터 업데이트
                    await mdb["user_weakness_data"].update_one(
                        {"user_id": user_id},
                        {
                            "$inc": {f"weakness.{syllable}.count": 1},
                            "$addToSet": {f"weakness.{syllable}.words": word}
                        },
                        upsert=True
                    )

        # 선택적으로, 약한 발음 리스트를 로깅하거나 반환
        # print("[LOG] Weak Syllables:", weak_syllables)
        # return weak_syllables

    except Exception as e:
        # 예외 처리 (로그 출력, HTTPException 등 상황에 맞게 처리)
        print(f"[오류] {e}")
        raise ValueError(f"약점 발음을 추출하는 중 오류 발생: {e}")


def preprocess_words(words: list) -> list:
    processed = [
        {
            "Word": w.get("Word"),
            "PronunciationAssessment": w.get("PronunciationAssessment"),
            "Syllables": [
                {
                    "Syllable": s.get("Syllable"),
                    "PronunciationAssessment": s.get("PronunciationAssessment")
                }
                for s in w.get("Syllables", [])
            ]
        }
        for w in words
    ]
    return processed

# 콜백을 통해 예외 로깅
def done_callback(task: asyncio.Task):
    try:
        task.result()  # 예외가 있으면 여기서 발생
        print("[LOG] 약점 발음분석이 정상적으로 종료되었습니다.")
    except Exception as e:
        print(f"[ERROR] 약점 발음분석 중 오류 발생: {e}")
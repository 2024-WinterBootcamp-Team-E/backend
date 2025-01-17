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

def extract_weak_pronunciations(azure_result, threshold=85):
    try:
        # result_properties 가져오기
        result_properties = azure_result.get("result_properties", {})
        json_string = None

        # JsonResult를 포함하는 키 검색
        for key, value in result_properties.items():
            if "JsonResult" in str(key):
                json_string = value
                break

        # JsonResult 데이터 확인
        if not json_string:
            raise ValueError("result_properties에서 JsonResult 데이터를 찾을 수 없습니다.")

        # JSON 문자열 디코딩
        json_data = json.loads(json_string)

        # NBest 데이터 확인
        nbest_data = json_data.get("NBest", [])
        if not nbest_data:
            raise ValueError("NBest 데이터가 비어 있습니다.")
        weak_syllables = []
        # NBest 섹션을 순회하며 분석
        for nbest in nbest_data:
            for word_data in nbest.get("Words", []):
                word = word_data.get("Word", "")
                for syllable_data in word_data.get("Syllables", []):
                    syllable = syllable_data.get("Syllable", "")
                    pronunciation_assessment = syllable_data.get("PronunciationAssessment", {})
                    accuracy_score = pronunciation_assessment.get("AccuracyScore", 100.0)

                    # 정확도 점수가 임계값 이하일 경우 약한 발음으로 추가
                    if accuracy_score <= threshold:
                        weak_syllables.append({
                            "word": word,
                            "syllable": syllable,
                            "accuracy_score": accuracy_score
                        })

        return weak_syllables

    except json.JSONDecodeError as e:
        print(f"[오류] JSON 디코딩 실패: {e}")
        raise ValueError("JsonResult가 올바른 JSON 형식이 아닙니다.")
    except Exception as e:
        print(f"[오류] {e}")
        raise ValueError(f"약점 발음을 추출하는 중 오류 발생: {e}")
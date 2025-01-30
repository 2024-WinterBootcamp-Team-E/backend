import io
from typing import Optional, Dict
from sqlalchemy import desc, func, cast, Date
from sqlalchemy.orm import Session, joinedload
from app.models.feedback import Feedback
from app.schemas.user import UserWithFeedback
from app.models.user import User
import json
from fastapi import HTTPException, UploadFile
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydub import AudioSegment
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
        json_data = json.loads(json_string)
        pronunciation_assessment = json_data.get("NBest", [{}])[0].get("PronunciationAssessment", {})
        value = pronunciation_assessment.get(key)
        if value is None:
            raise ValueError(f"키 {key}를 찾을 수 없습니다.")
        return float(value)
    except json.JSONDecodeError as e:
        print(f"[ERROR] JSON decoding failed: {e}")
        raise ValueError("JsonResult가 올바른 JSON 형식이 아닙니다.")
    except ValueError as e:
        print(f"[ERROR] {e}")
        raise
    return feedback

def get_avg_score(user_id: int, db: Session) -> Dict[str, Optional[float]]:
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
        # 약한 음절을 담을 리스트 (디버깅, 로깅 용도)
        weak_syllables = []
        for word_data in processed_words:
            word = word_data.get("Word", "")
            syllables = word_data.get("Syllables", [])
            for syllable_data in syllables:
                syllable = syllable_data.get("Syllable", "")
                pron_assessment = syllable_data.get("PronunciationAssessment", {})
                accuracy_score = pron_assessment.get("AccuracyScore", 100.0)
                # 음절이 2개보다 적을때 정확도 점수가 임계값 이하면 약한 발음으로 판단
                if len(syllable)<3 and accuracy_score <= threshold:
                    weak_syllables.append({
                        "word": word,
                        "syllable": syllable,
                        "accuracy_score": accuracy_score
                    })
                    await mdb["user_weakness_data"].update_one(
                        {"user_id": user_id},
                        {
                            "$inc": {f"weakness.{syllable}.count": 1},
                            "$addToSet": {f"weakness.{syllable}.words": word}
                        },
                        upsert=True
                    )
        print("[LOG] Weak Syllables:", weak_syllables)
    except Exception as e:
        print(f"[오류] {e}")
        raise ValueError(f"약점 발음을 추출하는 중 오류 발생: {e}")


def preprocess_words(words: list) -> dict:
    processed = []
    is_monotone_overall = False  # 전체 데이터의 isMonotone 플래그 초기화

    for w in words:
        if len(w.get("Word")) <=2:
            continue
        # PronunciationAssessment 정보 추출
        pa = w.get("PronunciationAssessment", {})
        accuracy_score = pa.get("AccuracyScore")
        error_type = pa.get("ErrorType")

        # Feedback > Prosody > Break > ErrorTypes 추출
        feedback = pa.get("Feedback", {})
        prosody = feedback.get("Prosody", {})
        break_info = prosody.get("Break", {})

        # 처리된 단어 정보 구성
        processed_word = {
            "Word": w.get("Word"),
            "PronunciationAssessment": {
                "AccuracyScore": accuracy_score,
                "ErrorType": error_type,
                "Break": break_info
            },
            "Syllables": w.get("Syllables", [])
        }

        processed.append(processed_word)

    intonation = prosody.get("Intonation", {})
    intonation_error_types = intonation.get("ErrorTypes", [])
    if(intonation_error_types != []):
        is_monotone_overall = True
    # 최종 반환: processed 리스트와 is_monotone_overall 플래그
    result = {
        "processed": processed,
        "isMonotone": is_monotone_overall
    }

    print(f"[LOG] preprocess : {result}.")
    return result

async def preprocess_words_async(words: list) -> dict:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, preprocess_words, words)
# 콜백을 통해 예외 로깅
def done_callback(task: asyncio.Task):
    try:
        task.result()
        print("[LOG] 약점 발음분석이 정상적으로 종료되었습니다.")
    except Exception as e:
        print(f"[ERROR] 약점 발음분석 중 오류 발생: {e}")

def change_audio_file(audio_file: UploadFile) -> bytes:
    try:
        audio = AudioSegment.from_file(audio_file.file)
        # 샘플링 속도, 채널, 샘플 포맷 설정
        audio = audio.set_frame_rate(16000)  # 16kHz
        audio = audio.set_channels(1)       # 모노
        audio = audio.set_sample_width(2)   # 16비트 (2 bytes per sample)
        # 변환된 데이터를 바이트로 반환
        wav_io = io.BytesIO()
        audio.export(wav_io, format="wav")
        wav_io.seek(0)
        return wav_io.read()
    except Exception as e:
        print(f"[ERROR] Audio conversion failed: {e}")
        raise HTTPException(status_code=400, detail="오디오 변환 중 오류가 발생했습니다.")

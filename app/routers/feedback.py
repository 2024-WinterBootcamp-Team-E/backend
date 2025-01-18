from fastapi import APIRouter, Depends, UploadFile, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db, get_mongo_db, get_mongo_async_db
from app.config.azure.pronunciation_feedback import analyze_pronunciation_with_azure
from app.schemas.ResultResponseModel import ResultResponseModel
from app.services.feedback_service import get_value, get_avg_score, extract_weak_pronunciations, preprocess_words
from app.models.sentence import Sentence
from app.config.openAI.openai_service import get_pronunciation_feedback
from app.models.feedback import Feedback
from app.services.user_service import get_user
from pymongo.database import Database
import asyncio

router = APIRouter(
    prefix="/feedback",
    tags=["Feedback"]
)

@router.post("/{user_id}/{sentence_id}", summary="발음 분석", description="Azure Speech SDK를 이용해 발음 평가 결과 반환 및 데이터 저장")
async def analyze_pronunciation_endpoint(
        user_id: int,
        sentence_id: int,
        audio_file: UploadFile,
        db: Session = Depends(get_db),
        mdb: Database = Depends(get_mongo_async_db)
):
    try:
        sentence_entry = db.query(Sentence).filter(Sentence.sentence_id == sentence_id,
                                                   Sentence.is_deleted == False).first()
        if not sentence_entry:
            raise HTTPException(status_code=404, detail="해당 문장을 찾을 수 없습니다.")
        text = sentence_entry.content
        # print(f"[LOG] Sentence Content: {text}")
        audio_data = await audio_file.read()
        azure_result = await analyze_pronunciation_with_azure(text, audio_data)

        nbest_list = azure_result.get("NBest")
        if not nbest_list:
            raise HTTPException(status_code=400, detail="NBest 데이터가 비어 있습니다.")
        nbest_data = nbest_list[0]
        words = nbest_data.get("Words")

        if not words:
            raise HTTPException(status_code=400, detail="Words 데이터가 비어 있습니다.")
        processed_words = preprocess_words(words)
        #print(f"[LOG] Azure Result: {processed_words}")

        pron_assessment = nbest_data.get("PronunciationAssessment")
        if not pron_assessment:
            raise HTTPException(status_code=400, detail="PronunciationAssessment 데이터가 없습니다.")
        keys = ["AccuracyScore", "FluencyScore", "CompletenessScore", "PronScore"]

        # 5) 점수 추출
        scores = {k: pron_assessment[k] for k in keys}

        # 디버깅 로그
        # for k, v in scores.items():
        #     print(f"[LOG] {k}: {v}")
        extract_task = asyncio.create_task(
            extract_weak_pronunciations(processed_words, user_id, mdb)
        )
        gpt_task = asyncio.create_task(
            get_pronunciation_feedback(processed_words, text)
        )

        #두 작업을 동시에 실행하고, 둘 다 끝날 때까지 대기
        gpt_result, _ = await asyncio.gather(gpt_task, extract_task)

        feedback_entry = db.query(Feedback).filter_by(user_id=user_id, sentence_id=sentence_id).first()
        if not feedback_entry:
            feedback_entry = Feedback(user_id=user_id, sentence_id=sentence_id)
            db.add(feedback_entry)
        feedback_entry.accuracy_score = scores["AccuracyScore"]
        feedback_entry.fluency_score = scores["FluencyScore"]
        feedback_entry.completeness_score = scores["CompletenessScore"]
        feedback_entry.pron_score = scores["PronScore"]
        feedback_entry.pronunciation_feedback = gpt_result
        db.commit()

        return {
            "sentence_content": text,
            "gpt_result": gpt_result,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"[ERROR] {e}")
        raise HTTPException(status_code=500, detail=f"발음 평가 중 오류가 발생했습니다: {str(e)}")

@router.get("/{user_id}/{sentence_id}/score", summary="최근 발음 평가 결과 평균 점수 조회", description="특정 사용자의 최근 발음 평가 평균 점수 결과 조회")
def get_user_avg_score(user_id: int, db: Session = Depends(get_db)):
    feedbacks_score = get_avg_score(user_id, db)
    user = get_user(user_id, db)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return ResultResponseModel(code=200, message="상황 문장 목록 조회 성공", data=feedbacks_score)
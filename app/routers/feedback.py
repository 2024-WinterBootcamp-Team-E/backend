import asyncio

from fastapi import APIRouter, Depends, UploadFile, HTTPException
from sqlalchemy.orm import Session
from starlette.responses import StreamingResponse
from app.database.session import get_db, get_mongo_async_db, get_mongo_db
from app.config.azure.pronunciation_feedback import analyze_pronunciation_with_azure
from app.schemas.ResultResponseModel import ResultResponseModel
from app.services.feedback_service import get_value, get_avg_score, preprocess_words, extract_weak_pronunciations, \
    done_callback, change_audio_file
from app.models.sentence import Sentence
from app.config.openAI.openai_service import get_pronunciation_feedback, sse_generator_wrapper
from app.models.feedback import Feedback
from app.services.user_service import get_user
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.database import Database

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
        mdb: AsyncIOMotorDatabase = Depends(get_mongo_async_db)
):
    try:
        sentence_entry = db.query(Sentence).filter_by(sentence_id=sentence_id, is_deleted=False).first()
        if not sentence_entry:
            raise HTTPException(status_code=404, detail="해당 문장을 찾을 수 없습니다.")
        text = sentence_entry.content
        #print(f"[LOG] Sentence Content: {text}
        change_audio = change_audio_file(audio_file)
        azure_result = await analyze_pronunciation_with_azure(text, change_audio)
        # print(f"[LOG] Azure Result: {azure_result}\n")
        # print(f"[LOG] Azure Result: {azure_result.get('RecognitionStatus')}")

        if azure_result.get('RecognitionStatus') != 'Success':
            raise HTTPException(status_code=400, detail="인식 실패: 다시 시도해 주세요.")
        nbest_list = azure_result.get("NBest")
        if not nbest_list:
            raise HTTPException(status_code=400, detail="NBest 데이터가 비어 있습니다.")
        nbest_data = nbest_list[0]
        words = nbest_data.get("Words")

        if not words:
            raise HTTPException(status_code=400, detail="Words 데이터가 비어 있습니다.")
        processed_words = preprocess_words(words)

        pron_assessment = nbest_data.get("PronunciationAssessment")
        if not pron_assessment:
            raise HTTPException(status_code=400, detail="PronunciationAssessment 데이터가 없습니다.")
        keys = ["AccuracyScore", "FluencyScore", "CompletenessScore", "PronScore"]

        #점수 추출
        scores = {k: pron_assessment[k] for k in keys}

        background_task = asyncio.create_task(
            extract_weak_pronunciations(processed_words, user_id, mdb, threshold=75)
        )
        background_task.add_done_callback(done_callback)

        feedback_generator = get_pronunciation_feedback(processed_words,text)
        wrapped_stream = sse_generator_wrapper(
            generator=feedback_generator,
            user_id=user_id,
            sentence_id=sentence_id,
            db=db,
            scores=scores,
            azure_result=azure_result
        )
        return StreamingResponse(
            wrapped_stream,                # async generator
            media_type="text/event-stream" # SSE MIME
        )

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


@router.get("/{user_id}/weak_pronunciations")
async def get_weak_pronunciations(user_id: int, db: Session = Depends(get_db), mdb: Database = Depends(get_mongo_db)):
    """
    사용자의 약한 음절 중 상위 5개의 음절과 관련 단어 반환
    """
    try:
        user = get_user(user_id, db)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        # 1) MongoDB에서 사용자 약점 데이터 조회
        user_data = mdb["user_weakness_data"].find_one({"user_id": user_id})

        if not user_data or "weakness" not in user_data:
            return ResultResponseModel(
                code=404,
                message="No weak pronunciations found for this user.",
                data=None
            )

        # 2) 약점 데이터에서 count 기반으로 상위 5개의 음절 추출
        weakness = user_data["weakness"]
        sorted_syllables = sorted(
            weakness.items(),
            key=lambda item: item[1].get("count", 0),
            reverse=True
        )[:5]

        # 3) 상위 5개의 음절 및 관련 단어를 준비
        result = [
            {
                "syllable": syllable,
                "count": data.get("count", 0),
                "words": data.get("words", [])
            }
            for syllable, data in sorted_syllables
        ]

        # 4) 정상 응답 반환
        return ResultResponseModel(
            code=200,
            message="약점 발음 반환 성공",
            data={"user_id": user_id, "top_weak_pronunciations": result}
        )

    except Exception as e:
        # 5) 에러 발생 시 응답
        return ResultResponseModel(
            code=500,
            message="An error occurred.",
            data={"error": str(e)}
        )
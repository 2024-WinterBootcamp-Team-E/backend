from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from app.services.speech_service import get_sentences_by_situation
from app.database.session import get_db
from app.schemas.ResultResponseModel import ResultResponseModel
from fastapi import APIRouter
from app.models.sentence import Sentence  # Sentence 모델 import

router = APIRouter(
    prefix="/speech",
    tags=["Speech"]
)


# 기존 상황 문장 목록 조회 API
@router.get("/situationType/all", summary="상황 문장 목록 조회", description="특정 상황 유형에 해당하는 모든 문장을 조회합니다.")
def fetch_sentences(situation: str, db: Session = Depends(get_db)):
    sentences = get_sentences_by_situation(situation, db)
    if not sentences:
        raise HTTPException(
            status_code=404,
            detail=f"No sentences found for situation: {situation}"
        )
    response_data = [sentence.content for sentence in sentences]
    return ResultResponseModel(code=200, message="상황 문장 목록 조회 성공", data=response_data)


# 새로운 문장 조회 API
@router.get("/{sentence_id}", summary="문장 조회", description="문장 ID를 기반으로 문장을 조회합니다.")
def fetch_sentence(sentence_id: int, db: Session = Depends(get_db)):
    sentence = db.query(Sentence).filter(Sentence.sentence_id == sentence_id).first()
    if not sentence:
        raise HTTPException(status_code=404, detail="Sentence not found")

    response_data = {
        "sentence_id": sentence.sentence_id,
        "content": sentence.content,
        "situation": sentence.situation,
        "voice_url": sentence.voice_url
    }
    return ResultResponseModel(code=200, message="문장 조회 성공", data=response_data)
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.speech_service import get_sentences_by_situation, get_sentence, get_pronunciation_feedback, \
    create_pronunciation_result, get_sentence_detail
from app.schemas.ResultResponseModel import ResultResponseModel


router = APIRouter(
    prefix="/speech",
    tags=["Speech"]
)

@router.get("/situationType/all", summary="상황 문장 목록 조회", description="특정 상황 유형에 해당하는 모든 문장을 조회합니다.")
def fetch_sentences(situation: str, db: Session = Depends(get_db)):
    sentences = get_sentences_by_situation(situation, db)
    if not sentences:
        raise HTTPException(status_code=404, detail=f"No sentences found for situation: {situation}")
    response_data = [sentence.content for sentence in sentences]
    return ResultResponseModel(code=200, message="상황 문장 목록 조회 성공", data=response_data)

@router.get("/{sentence_id}", summary="문장 조회", description="문장 ID를 기반으로 문장을 조회합니다.")
def fetch_sentence(sentence_id: int, db: Session = Depends(get_db)):
    sentence = get_sentence(sentence_id, db)
    if not sentence:
        raise HTTPException(status_code=404, detail="Sentence not found")
    response_data = get_sentence_detail(sentence)
    return ResultResponseModel(code=200, message="문장 조회 성공", data=response_data)


@router.post("/{user_id}/results", summary="발음 테스트 결과 반환", description="특정 사용자의 발음 테스트 결과를 반환합니다.")
def get_pronunciation_results(user_id: int, sentence_id: int, db: Session = Depends(get_db)):
    feedback = get_pronunciation_feedback(user_id, sentence_id, db)
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found for the given user and sentence")
    sentence = get_sentence(sentence_id, db)
    if not sentence:
        raise HTTPException(status_code=404, detail="Sentence not found")
    response_data = create_pronunciation_result(feedback, sentence)
    return ResultResponseModel(code=200, message="발음 테스트 결과 반환 성공", data=response_data)


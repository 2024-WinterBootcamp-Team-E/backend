from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from app.services.speech_service import get_situation_type, get_sentences_by_situation
from app.database.session import get_db
from app.schemas.ResultResponseModel import ResultResponseModel
from fastapi import APIRouter

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

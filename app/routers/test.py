from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session
from app.config.aws.s3Clent import upload_audio
from app.database.session import get_db
from app.models.sentence import Sentence
from app.schemas.ResultResponseModel import ResultResponseModel
from app.services.user_service import get_user
from app.services.test_service import dailytask
from datetime import datetime
router = APIRouter(
    prefix="/test",
    tags=["Test"]
)
@router.post("/save_audio_url", summary="음성 파일 URL 저장", description="음성 파일 URL을 저장합니다.")
async def save_audio_url(file: UploadFile, situation: str, sentence_id: int, db: Session = Depends(get_db)):
    file_url = await upload_audio(file, situation)
    try:
        sentence = db.query(Sentence).filter(Sentence.sentence_id == sentence_id).first()
        if not sentence:
            raise HTTPException(status_code=404, detail="해당 sentence_id가 없습니다.")
        sentence.voice_url = file_url
        db.commit()
        return {"message": "성공적으로 저장되었습니다.", "voice_url": file_url}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"데이터베이스 업데이트 실패: {str(e)}")

@router.get("/dailytask/{user_id}/{selected_day}", summary="사용자별 당일 학습 정보 조회", description="지정된 사용자의 당일날 학습한 내용을 반환합니다.")
def get_dailytask(user_id:int, selected_day:datetime, db: Session=Depends(get_db)):
    user = get_user(user_id, db)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    dailytask_response = dailytask(db, user_id, selected_day)
    return ResultResponseModel(code=200, message="당일 학습 정보 조회 성공", data=dailytask_response)

@router.get("/health")
async def health_check():
    return {"status": "healthy"}

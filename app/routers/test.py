from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session
from app.config.aws.s3Clent import upload_audio
from app.database.session import get_db
from app.models.sentence import Sentence
router = APIRouter(
    prefix="/test",
    tags=["Test"]
)
@router.post("/save_audio_url")
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

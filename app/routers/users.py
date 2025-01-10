from fastapi import status, APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.config.aws.s3Clent import upload_audio
from app.database.session import get_db
from app.schemas.ResultResponseModel import ResultResponseModel
from app.services.feedback_service import get_feedbacks
from app.models.sentence import Sentence
from app.schemas.user import UserUpdate, UserCreate
from app.services.user_service import get_all_users, update_user
from app.services.user_service import user_soft_delete, user_hard_delete, get_user, signup_user

router = APIRouter(
    prefix="/user",
    tags=["User"]
)

@router.post("/signup", summary="회원 가입", description="유저 정보를 생성")
def signup(user_create: UserCreate, db: Session = Depends(get_db)):
    user = signup_user(user_create, db)
    if user.email:
        raise HTTPException(status_code=404, detail="이미 존재하는 이메일입니다.")
    return ResultResponseModel(code=200, message="회원 가입 성공", data=user.user_id) # 유저 id를 반환하는건 user id 하나

@router.get("/users")
def read_users(db: Session = Depends(get_db)):
    users = get_all_users(db)
    return {"users": users}

@router.get("/{user_id}", summary="특정 사용자 조회", response_model=ResultResponseModel)
def get_only_user(user_id: int, db: Session = Depends(get_db)):
    user = get_user(user_id, db)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    user_with_feedback = get_feedbacks(user, db)
    return ResultResponseModel(code=200, message="특정 사용자 조회 성공", data=user_with_feedback)


@router.delete("/soft/{user_id}", summary="soft delete로 삭제합니다.", description="is_deleted 애트리뷰트를 true로 변환")
def delete_user(user_id : int, db: Session = Depends(get_db)):
    user = get_user(user_id, db)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    user_soft_delete(user, db)
    return ResultResponseModel(code=200, message="soft delete 완료", data=None)

@router.delete("/hard/{user_id}", summary="hard delete로 삭제합니다.", description="users 테이블에서 user_id에 해당하는 엔트리 삭제")
def delete_user(user_id : int, db: Session = Depends(get_db)):
    user = get_user(user_id, db)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user_hard_delete(user, db)
    return ResultResponseModel(code=200, message="hard delete 완료", data=None)


@router.patch("/{user_id}", summary="사용자 정보 업데이트", description="특정 사용자의 정보를 업데이트합니다.")
def update_existing_user(user_id: int, update_data: UserUpdate, db: Session = Depends(get_db)):
    user = get_user(user_id, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="사용자를 찾을 수 없습니다.")
    update_user(user, update_data, db)
    return ResultResponseModel(code=200, message="사용자 정보 업데이트", data=None)


@router.post("/save_audio_url")
async def save_audio_url(file: UploadFile, situation: str, sentence_id: int, db: Session = Depends(get_db)):
    # S3에 파일 업로드 및 URL 반환
    file_url = await upload_audio(file, situation)
    try:
        # DB에서 해당 sentence_id 조회
        sentence = db.query(Sentence).filter(Sentence.sentence_id == sentence_id).first()
        if not sentence:
            raise HTTPException(status_code=404, detail="해당 sentence_id가 없습니다.")

        # voice_url 업데이트
        sentence.voice_url = file_url
        db.commit()
        return {"message": "성공적으로 저장되었습니다.", "voice_url": file_url}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"데이터베이스 업데이트 실패: {str(e)}")
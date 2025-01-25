from fastapi import status, APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.config.aws.s3Clent import  upload_image
from app.database.session import get_db
from app.schemas.ResultResponseModel import ResultResponseModel
from app.schemas.user import UserUpdate, UserCreate, UserLogin, UserResponse
from app.models.user import User
from app.services.user_service import update_user, create_user_with_feedback, attendance_data, attendance_today
from app.services.user_service import user_soft_delete, user_hard_delete, get_user, signup_user
from datetime import datetime, timedelta
import json
router = APIRouter(
    prefix="/user",
    tags=["User"]
)

@router.post("/signup", summary="회원 가입", description="새로운 유저의 회원가입")
def signup(req: UserCreate, db: Session = Depends(get_db)):
    new_user = User(email=req.email, password=req.password, nickname=req.nickname,
                    created_at=datetime.utcnow(), is_deleted=False)
    try:
        saved_user = signup_user(new_user, db)
        return ResultResponseModel(code=200, message="회원가입 성공",data=saved_user.user_id)
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="중복된 이메일입니다.")

@router.post("/login", summary="로그인", description="유저의 로그인")
def login(req: UserLogin, db: Session = Depends(get_db)):
    authenticated_user = db.query(User).filter(User.email == req.email).first()
    if not authenticated_user:
        raise HTTPException(status_code=400, detail="존재하지 않는 이메일입니다.")
    if authenticated_user.password != req.password:
        raise HTTPException(status_code=400, detail="잘못된 비밀번호입니다.")
    return ResultResponseModel(code=200, message="로그인 성공", data=authenticated_user.user_id)

@router.get("/{user_id}", summary="특정 사용자 조회", response_model=ResultResponseModel)
def get_only_user(user_id: int, db: Session = Depends(get_db)):
    user = get_user(user_id, db)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    # user_with_feedback = create_user_with_feedback(user, db)
    user_response = UserResponse.model_validate(user)
    return ResultResponseModel(code=200, message="특정 사용자 조회 성공", data=user_response)


@router.put("/soft/{user_id}", summary="soft delete로 삭제합니다.", description="is_deleted 애트리뷰트를 true로 변환")
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
    return ResultResponseModel(code=200, message="사용자 정보 업데이트 완료", data=None)
@router.post("/{user_id}/image", summary="사용자 프로필 이미지 업로드", description="사용자의 프로필 이미지를 업로드합니다.")
async def profile_image_upload(file: UploadFile, user_id: int, db: Session = Depends(get_db)):
    try:
        file_url = await upload_image(file, "image")
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="해당 user_id가 없습니다.")
        user.user_image = file_url
        db.commit()
        return ResultResponseModel(code=200, message="이미지 성공적으로 저장되었습니다.", data=file_url)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"데이터베이스 업데이트 실패: {str(e)}")

@router.get("/attendance/{user_id}")
def get_recent_attendance(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(user_id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 초기화 (필요 시)
    if not user.attendance_data:
        attendance_data(db, user_id)

    # 당일 데이터 업데이트
    attendance_today(db, user_id)

    # 출석 데이터 반환
    attendance_data = json.loads(user.attendance_data) if user.attendance_data else []
    return {
        "user_id": user_id,
        "attendance_status": attendance_data
    }

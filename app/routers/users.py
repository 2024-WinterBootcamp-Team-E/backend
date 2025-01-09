from fastapi import status, APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.ResultResponseModel import ResultResponseModel
from app.services.feedback_service import get_feedbacks
from app.schemas.user import UserUpdate, UserCreate, UserLogin
from app.services.user_service import get_all_users, update_user
from app.services.user_service import user_soft_delete, user_hard_delete, get_user, signup_user
from app.models.user import User

router = APIRouter(
    prefix="/user",
    tags=["User"]
)

@router.post("/signup", summary="회원 가입", description="유저 정보를 생성")
def signup(user_create: UserCreate, db: Session = Depends(get_db)):
    user = signup_user(user_create, db)
    return ResultResponseModel(code=200, message="회원 가입 성공", data=user.user_id)

@router.post("/login", summary="로그인", description="유저의 로그인")
def login(user: UserLogin, db: Session = Depends(get_db)):
    authenticated_user = db.query(User).filter(User.email == user.email).first()
    if not authenticated_user:
        raise HTTPException(status_code=400, detail="존재하지 않는 이메일입니다.")
    if authenticated_user.password != user.password:
        raise HTTPException(status_code=400, detail="잘못된 비밀번호입니다.")
    return ResultResponseModel(code=200, message="로그인 성공", data=authenticated_user.user_id)


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



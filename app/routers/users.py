from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.ResultResponseModel import ResultResponseModel
from app.services.user_service import user_soft_delete, user_hard_delete, get_user, get_all_users
from app.services.feedback_service import get_feedbacks

router = APIRouter(
    prefix="/user",
    tags=["User"]
)

@router.get("/users")
def read_users(db: Session = Depends(get_db)):
    users = get_all_users(db)
    return {"users": users}

@router.get("/{user_id}", summary="특정 사용자 조회", response_model=ResultResponseModel)
def get_only_user(user_id: int, db: Session = Depends(get_db)):
    user = get_user(user_id, db) # user_id에 대한 유저 조회
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    user_with_feedback = get_feedbacks(user, db)
    return ResultResponseModel(code=200, message="특정 사용자 조회 성공", data=user_with_feedback)


@router.delete("/soft/{user_id}", summary="soft delete로 삭제합니다.", description="is_deleted 애트리뷰트를 true로 변환")
def delete_user(user_id : int, db: Session = Depends(get_db)):
    user = get_user(user_id, db) # user_id에 대한 유저 조회
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    user_soft_delete(user, db)
    return ResultResponseModel(code=200, message="soft delete 완료", data=None)

@router.delete("/hard/{user_id}", summary="hard delete로 삭제합니다.", description="users 테이블에서 user_id에 해당하는 엔트리 삭제")
def delete_user(user_id : int, db: Session = Depends(get_db)):
    user = get_user(user_id, db)  # user_id에 대한 유저 조회
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user_hard_delete(user, db)
    return ResultResponseModel(code=200, message="hard delete 완료", data=None)

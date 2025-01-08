from fastapi import status, APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.ResultResponseModel import ResultResponseModel
from app.schemas.user import UserUpdate
from app.services.user_service import get_all_users, update_user
from app.services.user_service import user_soft_delete, user_hard_delete, get_user

router = APIRouter(
    prefix="/user",
    tags=["User"]
)

@router.get("/users")
def read_users(db: Session = Depends(get_db)):
    users = get_all_users(db)
    return {"users": users}


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


@router.patch("/{user_id}", summary="사용자 정보 업데이트", description="특정 사용자의 정보를 업데이트합니다.")
def update_existing_user(user_id: int, update_data: UserUpdate, db: Session = Depends(get_db)):
    user = get_user(user_id, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="사용자를 찾을 수 없습니다.")
    update_user(user, update_data, db)
    return ResultResponseModel(code=200, message="사용자 정보 업데이트", data=None)


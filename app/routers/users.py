from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.user_service import get_all_users
from app.models.user import User
from app.services.user_service import user_soft_delete, user_hard_delete

router = APIRouter(
    prefix="/user",
    tags=["User"]
)

@router.get("/users")
def read_users(db: Session = Depends(get_db)):
    """
    사용자 목록 조회 API
    """
    users = get_all_users(db)
    return {"users": users}


@router.delete("/user/soft/{user_id}")
def delete_user(user_id : int, db: Session = Depends(get_db)):
    user = db.get(User, user_id)  # user_id에 대한 유저 조회

    # 유저가 없을 경우 예외 처리
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    user_soft_delete(user, db)

    return {"message": f"User {user_id} is soft deleted"}

@router.delete("/user/hard/{user_id}")
def delete_user(user_id : int, db: Session = Depends(get_db)):
    user = db.get(User, user_id)  # user_id에 대한 유저 조회

    # 유저가 없을 경우 예외 처리
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user_hard_delete(user, db)

    return {"message": f"User {user_id} is hard deleted"}

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models.user import User
from fastapi import HTTPException
def get_all_users(db: Session):
    return db.query(User).all()

def get_user(user_id : int, db: Session):
    return db.get(User, user_id)

def user_soft_delete(user: User, db: Session):
    user.is_deleted = True  # is_deleted 필드를 True로... (soft delete)
    db.commit()  # 변경 사항 커밋
    db.refresh(user)  # 세션에서 객체 새로고침

def user_hard_delete(user: User, db: Session):
    try:
        # 테이블에서 사용자 삭제
        db.rollback()  # 트랜잭션 롤백
        db.delete(user)
        db.commit()  # 변경사항 커밋
    except IntegrityError as e:
        raise HTTPException(status_code=500, detail="Failed to delete user due to integrity constraints")

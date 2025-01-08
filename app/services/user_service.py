from sqlalchemy.orm import Session
from app.models.user import User

def get_all_users(db: Session):
    return db.query(User).all()

def get_user(user_id : int, db: Session):
    return db.get(User, user_id)

def user_soft_delete(user: User, db: Session):
    user.is_deleted = True  # is_deleted 필드를 True로... (soft delete)
    db.commit()  # 변경 사항 커밋
    db.refresh(user)  # 세션에서 객체 새로고침

def user_hard_delete(user: User, db: Session):
    db.delete(user)
    db.commit()  # 변경사항 커밋

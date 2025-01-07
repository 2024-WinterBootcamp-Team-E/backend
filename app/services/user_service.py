from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import status

from app.models.user import User
from fastapi import HTTPException

from app.schemas.user import UserUpdate, UserPasswordUpdate


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

def update_user(user: User, update_data: UserUpdate, db: Session):

    update_fields = update_data.model_dump(exclude_unset=True)  # 설정된 필드만 추출
    user.nickname = update_fields.get("nickname")  # nickname 필드 업데이트

    try:
        db.commit()  # 변경 사항 커밋
        db.refresh(user)  # 세션에서 객체 새로고침
        return user
    except IntegrityError as e:
        db.rollback()  # 오류 발생 시 롤백
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Integrity error: 중복된 값이나 유효하지 않은 데이터가 포함되어 있습니다."
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자 업데이트 중 오류가 발생했습니다."
        )


def update_user_password(user: User, update_data: UserPasswordUpdate, db: Session):
    user.password = update_data.new_password
    try:
        db.commit()  # 변경 사항 커밋
        db.refresh(user)  # 세션에서 객체 새로고침
        return user
    except IntegrityError as e:
        db.rollback()  # 오류 발생 시 롤백
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Integrity error: 중복된 값이나 유효하지 않은 데이터가 포함되어 있습니다."
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자 업데이트 중 오류가 발생했습니다."
        )
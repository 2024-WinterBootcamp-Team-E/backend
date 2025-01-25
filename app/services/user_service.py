from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import status
from app.models import Feedback
from app.models.user import User
from app.models.chat import Chat
from fastapi import HTTPException
from app.schemas.user import UserUpdate, UserWithFeedback
from datetime import datetime, timedelta
import json

def get_all_users(db: Session):
    return db.query(User).all()

def create_user_with_feedback(user: User, db: Session) -> UserWithFeedback:
    feedbacks = db.query(Feedback).filter(Feedback.user_id == user.user_id).all()
    user_with_feedback = UserWithFeedback(
        user_id=user.user_id,
        email=user.email,
        nickname=user.nickname,
        feedbacks=feedbacks
    )
    return user_with_feedback
def get_user(user_id : int, db: Session):
    return db.get(User, user_id)

def user_soft_delete(user: User, db: Session):
    user.is_deleted = True
    db.commit()
    db.refresh(user)

def user_hard_delete(user: User, db: Session):
    db.query(User).filter(User.user_id == user.user_id).delete()
    db.commit()

def update_user(user: User, update_data: UserUpdate, db: Session):
    user.nickname = update_data.nickname
    try:
        db.commit()
        db.refresh(user)
        return user
    except IntegrityError as e:
        db.rollback()
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

def signup_user(user: User, db: Session) -> User:
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def attendance_data(db: Session, user_id: int):
    user = db.query(User).filter_by(user_id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    today = datetime.utcnow().date()
    attendance_data = []

    # 과거 365일의 출석 상태를 계산
    for day_offset in range(365):
        date_to_check = today - timedelta(days=day_offset)
        start_time = datetime(date_to_check.year, date_to_check.month, date_to_check.day)
        end_time = start_time + timedelta(days=1)

        chats_activity = db.query(Chat).filter(
            Chat.user_id == user_id,
            ((Chat.created_at >= start_time) & (Chat.created_at < end_time)) |
            ((Chat.updated_at >= start_time) & (Chat.updated_at < end_time)),
            Chat.is_deleted == False
        ).count()

        feedbacks_activity = db.query(Feedback).filter(
            Feedback.user_id == user_id,
            ((Feedback.created_at >= start_time) & (Feedback.created_at < end_time)) |
            ((Feedback.updated_at >= start_time) & (Feedback.updated_at < end_time)),
            Feedback.is_deleted == False
        ).count()

        status = 2 if chats_activity > 0 and feedbacks_activity > 0 else 1 if chats_activity > 0 or feedbacks_activity > 0 else 0
        attendance_data.append(status)

    # 저장
    user.attendance_update = today
    user.attendance_data = json.dumps(list(reversed(attendance_data)))  # 최신 날짜가 마지막에 오도록 저장
    db.commit()

def attendance_today(db: Session, user_id: int):
    user = db.query(User).filter_by(user_id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    today = datetime.utcnow().date()
    start_time = datetime(today.year, today.month, today.day)
    end_time = start_time + timedelta(days=1)

    chats_activity = db.query(Chat).filter(
        Chat.user_id == user_id,
        ((Chat.created_at >= start_time) & (Chat.created_at < end_time)) |
        ((Chat.updated_at >= start_time) & (Chat.updated_at < end_time)),
        Chat.is_deleted == False
    ).count()

    feedbacks_activity = db.query(Feedback).filter(
        Feedback.user_id == user_id,
        ((Feedback.created_at >= start_time) & (Feedback.created_at < end_time)) |
        ((Feedback.updated_at >= start_time) & (Feedback.updated_at < end_time)),
        Feedback.is_deleted == False
    ).count()


    status = 2 if chats_activity > 0 and feedbacks_activity > 0 else 1 if chats_activity > 0 or feedbacks_activity > 0 else 0

    # 출석 데이터 업데이트
    attendance_data = json.loads(user.attendance_data) if user.attendance_data else []

    if len(attendance_data) > 0 and len(attendance_data) >= (
            datetime.utcnow().date() - (datetime.utcnow().date() - timedelta(len(attendance_data)))).days:
        attendance_data[-1] = status
    else:
        attendance_data.append(status)

        # 최대 365일의 데이터만 유지
    if len(attendance_data) > 365:
        attendance_data.pop(0)

        # 데이터 업데이트
    user.last_attendance_update = today
    user.attendance_data = json.dumps(attendance_data)
    db.commit()

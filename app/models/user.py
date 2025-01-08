from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from app.database.session import Base
from sqlalchemy.orm import relationship

# User 모델 정의
class User(Base):
    __tablename__ = 'users'

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    id = Column(String(20),nullable=False)
    password = Column(String(20),nullable=False)
    nickname = Column(String(20), nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    modified_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    is_deleted = Column(Boolean, nullable=False, default=False)

    chats = relationship("Chat", back_populates="user")
    feedbacks = relationship("Feedback", back_populates="user")
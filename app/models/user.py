from sqlalchemy import Column, Integer, String, Boolean, DateTime, func, Text, Date
from sqlalchemy.orm import relationship
from app.database.session import Base
class User(Base):
    __tablename__ = 'users'

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255),nullable=False, unique=True)
    password = Column(String(255),nullable=False)
    nickname = Column(String(50), nullable=False)
    user_image = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    is_deleted = Column(Boolean, default=False)
    attendance_update = Column(Date, nullable=True)
    attendance_data = Column(Text, nullable=True)

    chats = relationship("Chat", back_populates="user")
    feedbacks = relationship("Feedback", back_populates="user")
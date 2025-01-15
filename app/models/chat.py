from sqlalchemy import Column, Integer, ForeignKey, Text, DateTime, func, Boolean,String
from sqlalchemy.orm import relationship
from app.database.session import Base
class Chat(Base):
    __tablename__ = 'chats'

    chat_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    score = Column(Integer, nullable=True)
    subject = Column(Text, nullable=True)
    character_name = Column(String(10), nullable=True)
    tts_id = Column(String(50), nullable=True)  # TTS ID
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    is_deleted = Column(Boolean, default=False)

    user = relationship("User", back_populates="chats")


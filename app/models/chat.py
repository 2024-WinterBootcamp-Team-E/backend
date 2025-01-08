from sqlalchemy import Column, Integer, ForeignKey, Text, DateTime, func, Boolean
from sqlalchemy.orm import relationship
from app.database.session import Base

class Chat(Base):
    __tablename__ = 'chats'

    chat_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    character_id = Column(Integer, ForeignKey("characters.character_id"), nullable=False)
    score = Column(Integer, nullable=True)
    situation = Column(Text, nullable=False)
    created_at = Column(DateTime, default=func.now())
    update_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    is_deleted = Column(Boolean, nullable=False, default=False)

    user = relationship("User", back_populates="chats")
    character = relationship("Character", back_populates="chats")


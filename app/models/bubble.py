from sqlalchemy import Column, Integer, ForeignKey, Text, DateTime, func, Boolean
from sqlalchemy.orm import relationship
from app.database.session import Base
class Chat(Base):
    __tablename__ = 'bubbles'

    chat_history_id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(Integer, ForeignKey('chats.chat_id'), nullable=False)
    content = Column(Text, nullable=True)
    grammar_feedback = Column(Text, nullable=True)
    speaker=Column(Boolean, default=False)

    chat = relationship("Chat", back_populates="bubbles",cascade="all, delete-orphan")


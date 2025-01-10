from sqlalchemy import Column, String, Text, DateTime, Integer
from sqlalchemy.sql import func
from app.database.session import Base
from sqlalchemy.orm import relationship

class Character(Base):
    __tablename__ = 'characters'

    character_id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String(10), nullable=False, unique=True)
    description = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    chats = relationship("Chat", back_populates="character", cascade="all, delete-orphan")

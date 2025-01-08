from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.sql import func
from app.database.session import Base
from sqlalchemy.orm import relationship

class Sentence(Base):
    __tablename__ = 'sentences'

    sentence_id = Column(Integer, primary_key=True, autoincrement=True)
    voice_url = Column(String(50), nullable=False)
    content = Column(String(100), nullable=False)
    situation = Column(String(20), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    deleted_at = Column(Boolean, nullable=False, default=False)


    # Relationships
    feedbacks = relationship("Feedback", back_populates="sentence")

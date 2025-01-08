from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Float, ForeignKey
from sqlalchemy.sql import func
from app.database.session import Base
from sqlalchemy.orm import relationship

class Feedback(Base):
    __tablename__ = 'feedbacks'

    feedback_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    sentence_id = Column(Integer, ForeignKey("sentences.sentence_id"), nullable=False)
    accuracy = Column(Float, nullable=False)
    content = Column(Text, nullable=False)
    pronunciation_feedback = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    deleted_at = Column(Boolean, nullable=False, default=False)

    user = relationship("User", back_populates="feedbacks")
    sentence = relationship("Sentence", back_populates="feedbacks")
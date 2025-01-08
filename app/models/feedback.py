from sqlalchemy import Column, Integer, DateTime, Float, ForeignKey, Text, func, Boolean
from sqlalchemy.orm import relationship
from app.database.session import Base

class Feedback(Base):
    __tablename__ = 'feedbacks'

    feedback_id = Column(Integer, primary_key=True, autoincrement=True)
    sentence_id = Column(Integer, ForeignKey("sentences.sentence_id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    accuracy = Column(Float, nullable=False)
    content = Column(Text, nullable=True)
    feedback = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    is_deleted = Column(Boolean, nullable=False, default=False)

    user = relationship("User", back_populates="feedbacks")
    sentence = relationship("Sentence", back_populates="feedback")

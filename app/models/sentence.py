from sqlalchemy import Column, Integer, String, DateTime, func, Boolean
from sqlalchemy.orm import relationship
from app.database.session import Base

class Sentence(Base):
    __tablename__ = 'sentences'

    sentence_id = Column(Integer, primary_key=True, autoincrement=True)
    content = Column(String(100), nullable=True)
    situation = Column(String(20), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    is_deleted = Column(Boolean, nullable=False, default=False)

    feedback = relationship("Feedback", back_populates="sentence")
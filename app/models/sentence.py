from sqlalchemy import Column, Integer, String, DateTime, func, Boolean, Enum, Text
from sqlalchemy.orm import relationship
from app.database.session import Base
import enum
class SituationType(enum.Enum):
    TRAVEL = "여행"
    BUSINESS = "비즈니스"
    DAILY = "일상"
    MOVIE = "영화"
class Sentence(Base):
    __tablename__ = 'sentences'

    sentence_id = Column(Integer, primary_key=True, autoincrement=True)
    situation = Column(Enum(SituationType), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    is_deleted = Column(Boolean, default=False)
    content = Column(String(255), nullable=False)
    voice_url = Column(Text, nullable=False)

    feedbacks = relationship("Feedback", back_populates="sentence")
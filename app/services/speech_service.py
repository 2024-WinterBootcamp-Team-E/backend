from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.sentence import Sentence, SituationType

# 상황 유형 조회
def get_situation_type():
    return [situation.value for situation in SituationType]

situation_mapping = {
    "여행": "TRAVEL",
    "비즈니스": "BUSINESS",
    "일상": "DAILY",
    "영화": "MOVIE"
}

# 특정 상황에 대한 문장 목록 조회
def get_sentences_by_situation(situation: str, db: Session):
    # 요청 값을 Enum의 name 또는 value로 매핑
    try:
        if situation in [s.value for s in SituationType]:  # 요청 값이 Enum의 value인지 확인
            situation_enum = next(s for s in SituationType if s.value == situation)
        else:  # 요청 값이 name인지 확인
            situation_enum = SituationType[situation]
    except (KeyError, StopIteration):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid situation!. Valid values are: {[s.value for s in SituationType]}"
        )
    # 데이터베이스에서 필터링
    return db.query(Sentence).filter_by(situation=situation_enum.name).all()
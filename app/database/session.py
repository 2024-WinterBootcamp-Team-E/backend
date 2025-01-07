import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 환경 변수에서 데이터베이스 URL 가져오기
DB_URL = os.getenv("DB_URL")

# 데이터베이스 엔진 생성
engine = create_engine(DB_URL, echo=True)  # echo=True로 SQLAlchemy 쿼리 로그 출력
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base 클래스 생성
Base = declarative_base()
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
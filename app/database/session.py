import os
from contextlib import asynccontextmanager
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from pymongo import MongoClient
from fastapi import FastAPI, Request

load_dotenv()

DB_URL = os.getenv("DB_URL")
engine = create_engine(DB_URL, echo=True)  # echo=True로 SQLAlchemy 쿼리 로그 출력
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


MONGODB_URL = os.getenv("MONGODB_URL")

# MongoDB Lifespan 관리
@asynccontextmanager
async def lifespan(app: FastAPI):
    # MongoDB 클라이언트 초기화
    print("MongoDB 클라이언트 초기화 중...")
    client = MongoClient(MONGODB_URL)
    try:
        app.state.mongo_client = client  # 애플리케이션 상태에 저장
        yield  # Lifespan 관리: 클라이언트가 앱 실행 동안 유지됨
    finally:
        print("MongoDB 클라이언트 종료 중...")
        client.close()


def get_mongo_db(request: Request):
    return request.app.state.mongo_client["winterboote"]
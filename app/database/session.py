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
engine = create_engine(DB_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


MONGODB_URL = os.getenv("MONGODB_URL")

@asynccontextmanager
async def lifespan(app: FastAPI):

    print("MongoDB 클라이언트 초기화 중...")
    client = MongoClient(MONGODB_URL)
    try:
        app.state.mongo_client = client
        yield
    finally:
        print("MongoDB 클라이언트 종료 중...")
        client.close()


def get_mongo_db(request: Request):
    return request.app.state.mongo_client["winterboote"]
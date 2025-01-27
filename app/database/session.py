import os
from contextlib import asynccontextmanager
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from pymongo import MongoClient
from fastapi import FastAPI, Request
import logging
from motor.motor_asyncio import AsyncIOMotorClient

logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

load_dotenv()

DB_URL = os.getenv("DB_URL")

engine = create_engine(f"{DB_URL}", echo=True)

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
    sync_client = MongoClient(MONGODB_URL)
    async_client = AsyncIOMotorClient(MONGODB_URL)
    app.state.mongo_sync_client = sync_client
    app.state.mongo_async_client = async_client
    try:
        yield
    finally:
        print("MongoDB 클라이언트 종료 중...")
        sync_client.close()
        async_client.close()

def get_mongo_db(request: Request):
    return request.app.state.mongo_sync_client["winterboote"]

def get_mongo_async_db(request: Request):
    return request.app.state.mongo_async_client["winterboote"]

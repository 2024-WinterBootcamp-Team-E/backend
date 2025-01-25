from fastapi import FastAPI
from app.database.session import Base, engine
from app.routers.api import router
from app.database.session import lifespan
from prometheus_fastapi_instrumentator import Instrumentator
from fastapi.middleware.cors import CORSMiddleware
import app.models
from dotenv import load_dotenv
import os

#Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
load_dotenv()
cors_origins = os.getenv("CORS_ORIGINS", "")
origins = cors_origins.split(",")

app = FastAPI(
    title="English API",
    description="English Speech Test API",
    version="1.0.0",
    lifespan=lifespan  # MongoDB Lifespan 관리 연결
)
instrumentator = Instrumentator().instrument(app)
instrumentator.expose(app, include_in_schema=False) # 메트릭 정보 확인

# CORS 설정 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,   # 허용할 출처를 명시합니다. '*'로 모든 출처 허용도 가능.
    allow_credentials=True,
    allow_methods=["*"],  # 허용할 HTTP 메서드 목록. '*'는 모든 메서드 허용.
    allow_headers=["*"],  # 허용할 헤더 목록. '*'는 모든 헤더 허용.
)
app.include_router(router)

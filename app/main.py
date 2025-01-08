from fastapi import FastAPI
from app.database.session import Base, engine
from app.routers.api import router
import app.models

# 데이터베이스 초기화
Base.metadata.create_all(bind=engine)

# FastAPI 앱 생성
app = FastAPI(
    title="English API",
    description="English Speech Test API",
    version="1.0.0",
)

# 라우터 등록
app.include_router(router)

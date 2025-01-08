from fastapi import FastAPI
from app.database.session import Base, engine
from app.routers.api import router
import app.models  # app/models/__init__.py를 통해 모든 모델 로드

# 데이터베이스 초기화
#Base.metadata.drop_all(bind=engine)  # 기존 테이블 삭제
Base.metadata.create_all(bind=engine)

# FastAPI 앱 생성
app = FastAPI(
    title="English API",
    description="English Speech Test API",
    version="1.0.0",
)

# 라우터 등록
app.include_router(router)

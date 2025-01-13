from fastapi import FastAPI
from app.database.session import Base, engine
from app.routers.api import router
from app.database.session import lifespan
import app.models

#Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="English API",
    description="English Speech Test API",
    version="1.0.0",
    lifespan=lifespan  # MongoDB Lifespan 관리 연결
)

app.include_router(router)

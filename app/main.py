from fastapi import FastAPI
from app.database.session import Base, engine
from app.routers.api import router
import app.models

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="English API",
    description="English Speech Test API",
    version="1.0.0",
)

app.include_router(router)

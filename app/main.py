from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from app.database.session import Base, engine, SessionLocal
from app.models import user

# 데이터베이스 초기화
Base.metadata.create_all(bind=engine)

# FastAPI 앱 생성
app = FastAPI()

# 의존성 주입: 데이터베이스 세션
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 라우트 예제
@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

# 사용자 조회 API 예제
@app.get("/users/")
def get_users(db: Session = Depends(get_db)):
    users = db.query(user).all()
    return users

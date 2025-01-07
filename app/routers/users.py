from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.user import get_all_users

router = APIRouter(
    prefix="/user",
    tags=["User"]
)

@router.get("/users")
def read_users(db: Session = Depends(get_db)):
    """
    사용자 목록 조회 API
    """
    users = get_all_users(db)
    return {"users": users}

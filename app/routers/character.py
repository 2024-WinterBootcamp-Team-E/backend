from fastapi import Depends
from sqlalchemy.orm import Session
from app.services.character_service import get_character
from app.database.session import get_db
from fastapi import APIRouter

router = APIRouter(
    prefix="/character",
    tags=["Character"]
)

@router.get("/", summary="캐릭터 목록 조회", description=" 캐릭터 목록을 조회합니다.")
def fetch_sentences(db: Session = Depends(get_db)):
    character = get_character(db)
    return {"characters": character}
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.schemas.ResultResponseModel import ResultResponseModel
# from app.services.character_service import get_characters
from app.database.session import get_db
from app.schemas.character import CharacterResponse
from fastapi import APIRouter
#
# router = APIRouter(
#     prefix="/character",
#     tags=["Character"]
# )
#
# @router.get("/", summary="캐릭터 목록 조회", description=" 캐릭터 목록을 조회합니다.", response_model=ResultResponseModel)
# def fetch_sentences(db: Session = Depends(get_db)):
#     characters = get_characters(db)
#     character_responses = list(map(CharacterResponse.model_validate, characters))
#     return ResultResponseModel(code=200, message="캐릭터 조회 완료", data=character_responses)
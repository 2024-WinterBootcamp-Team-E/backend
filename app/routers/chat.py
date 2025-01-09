from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.chat_service import delete_chat, get_chat
from app.schemas.ResultResponseModel import ResultResponseModel
from app.services.user_service import get_user
from app.schemas.chat import ChatResponse

router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)
@router.delete("/{user_id}/{chat_id}", summary="Chatroom 삭제", description="특정 user_id와 chat_id에 해당하는 채팅방을 삭제합니다.")
def delete_chatroom(user_id: int, chat_id: int, db: Session = Depends(get_db)):
    user = get_user(user_id, db)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    chat = get_chat(user_id=user_id, chat_id=chat_id, db=db)
    if not chat:
        raise HTTPException(status_code=404, detail="Chatroom not found")
    delete_chat(chat, db)
    return ResultResponseModel(code=200, message="Chatroom deleted successfully", data=None)

@router.get("/{user_id}/{chat_id}", summary="특정 채팅방 조회", description="특정 user_id와 chat_id에 해당하는 채팅방 정보를 반환합니다.")
def get_chat_detail(user_id: int, chat_id: int, db: Session = Depends(get_db)):
    user = get_user(user_id, db)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    chat = get_chat(user_id=user_id, chat_id=chat_id, db=db)
    if not chat:
        raise HTTPException(status_code=404, detail="Chatroom not found")
    chat_response = ChatResponse.model_validate(chat)
    return ResultResponseModel(code=200, message="Chatroom retrieved successfully", data=chat_response)


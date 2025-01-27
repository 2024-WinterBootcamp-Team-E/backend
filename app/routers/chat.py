import io
from fastapi import APIRouter, Depends, HTTPException,UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pymongo.database import Database
from app.config.constants import CHARACTER_TTS_MAP
from app.database.session import get_db, get_mongo_db
from app.services.chat_service import delete_chat, get_chat, get_chatrooms, create_chatroom, create_chatroom_mongo, \
    get_chat_history, event_generator
from app.schemas.ResultResponseModel import ResultResponseModel
from app.services.user_service import get_user
from app.schemas.chat import ChatRoomCreateRequest

router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)

@router.get("/{user_id}", summary="모든 채팅방 조회", description="그 유저에 대한 모든 회화채팅방 목록을 반환합니다.")
def get_all_chatrooms(user_id: int, db: Session = Depends(get_db), skip: int = 0, limit: int = 100):
    user = get_user(user_id, db)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    chatrooms = get_chatrooms(user_id=user_id, db=db, skip=skip, limit=limit)
    return ResultResponseModel(code=200,message="모든 채팅방 조회 완료",data=chatrooms)

@router.delete("/{user_id}/{chat_id}", summary="Chatroom 삭제", description="특정 user_id와 chat_id에 해당하는 채팅방을 삭제합니다.")
def delete_chatroom(user_id: int, chat_id: int, mdb: Database = Depends(get_mongo_db), db: Session = Depends(get_db)):
    user = get_user(user_id, db)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    chat = get_chat(user_id=user_id, chat_id=chat_id, db=db)
    if not chat:
        raise HTTPException(status_code=404, detail="Chatroom not found")
    delete_chat(chat, mdb, db)
    return ResultResponseModel(code=200, message="Chatroom deleted successfully", data=None)

@router.get("/{user_id}/{chat_id}", summary="특정 채팅방 조회", description="특정 user_id와 chat_id에 해당하는 채팅방 정보를 반환합니다.")
def get_chatroom_detail(user_id: int, chat_id: int, db: Session = Depends(get_db), mdb: Database = Depends(get_mongo_db)):
    user = get_user(user_id, db)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    chat = get_chat(user_id=user_id, chat_id=chat_id, db=db)
    if not chat:
        raise HTTPException(status_code=404, detail="Chatroom not found")
    chat_history = get_chat_history(chat_id, mdb)
    if not chat_history:
        raise HTTPException(status_code=404, detail="mongodb: Chat history not found")
    response_data = {
        "chat_history": chat_history.get("messages", [])
    }
    return ResultResponseModel(code=200, message="Chatroom retrieved successfully", data=response_data)

@router.post("/{user_id}/chat", summary="채팅방생성", description="새로운 채팅방을 생성합니다.")
def chat_with_voice(req: ChatRoomCreateRequest, user_id: int, db: Session = Depends(get_db),mdb: Database = Depends(get_mongo_db)):
    user = get_user(user_id, db)
    if not user:
        raise HTTPException(status_code=404, detail="사용자 없음")
    tts_id = CHARACTER_TTS_MAP.get(req.character_name)
    if not tts_id:
        raise HTTPException(status_code=400, detail="유효하지 않은 캐릭터 이름입니다.")

    new_chat = create_chatroom(req, user_id, db)
    create_chatroom_mongo(new_chat, mdb)
    return ResultResponseModel(code=200, message="채팅방 생성 완료", data=new_chat)

@router.post("/{user_id}/{chat_id}", summary="대화 생성", description="STT를 통해 GPT와 대화를 생성합니다.",response_class=StreamingResponse)
async def create_bubble(chat_id: int,user_id: int, file: UploadFile, db: Session = Depends(get_db), mdb: Database = Depends(get_mongo_db)):
    user = get_user(user_id, db)
    if not user:
        raise HTTPException(status_code=404, detail="사용자 없음")
    chat = get_chat(user_id=user_id, chat_id=chat_id, db=db)
    if not chat:
        raise HTTPException(status_code=404, detail="채팅방을 찾을 수 없습니다.")
    title = chat.title
    country = chat.character_name
    event = event_generator(chat_id=chat_id, tts_id=chat.tts_id, file_content_io=io.BytesIO(await file.read()),filename=file.filename, title=title, country=country, mdb=mdb)
    return StreamingResponse(event, media_type="text/event-stream")
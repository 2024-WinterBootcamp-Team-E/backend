import base64

from fastapi import APIRouter, Depends, HTTPException,UploadFile
from sqlalchemy.orm import Session
from pymongo.database import Database

from app.config.constants import CHARACTER_TTS_MAP
from app.config.elevenlabs.text_to_speech_stream import text_to_speech_data
from app.config.openAI.openai_service import transcribe_audio
from app.database.session import get_db, get_mongo_db
from app.services import character_service, chat_service
from app.services.chat_service import delete_chat, get_chat, get_chatrooms, create_chatroom, create_chatroom_mongo, \
    get_chat_history
from app.schemas.ResultResponseModel import ResultResponseModel
from app.services.user_service import get_user
from app.schemas.chat import ChatResponse,ChatRoomCreateRequest

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
    if not chatrooms:
        raise HTTPException(status_code=404, detail="채팅방을 찾을 수 없습니다.")
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
    chat_response = ChatResponse.model_validate(chat)
    chat_history = get_chat_history(chat_id, mdb)
    response_data = {
        "chat_info": chat_response,
        "chat_history": chat_history.get("messages", [])  # MongoDB에서 messages 배열만 추출
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

    new_chat = create_chatroom(req, user_id, tts_id, db)
    create_chatroom_mongo(new_chat, mdb)
    return ResultResponseModel(code=200, message="채팅방 생성 완료", data=new_chat.chat_id)


@router.post("/{user_id}/{chat_id}", summary="대화 생성", description="STT를 통해 GPT와 대화를 생성합니다.")
async def create_bubble(chat_id: int,user_id: int, file: UploadFile, db: Session = Depends(get_db), mdb: Database = Depends(get_mongo_db)):
    user = get_user(user_id, db)
    if not user:
        raise HTTPException(status_code=404, detail="사용자 없음")
    chat = get_chat(user_id=user_id, chat_id=chat_id, db=db)
    if not chat:
        raise HTTPException(status_code=404, detail="채팅방을 찾을 수 없습니다.")
    try:
        transcription = transcribe_audio(file)
        tts_id = CHARACTER_TTS_MAP.get(chat.character_name)
        response = chat_service.create_bubble_result(chat_id=chat_id, transcription=transcription, mdb=mdb)
        tts_audio = text_to_speech_data(text=response["gpt_response"], voice_id=tts_id)
        tts_audio.seek(0)

        tts_audio_base64 = base64.b64encode(tts_audio.getvalue()).decode("utf-8")
        return {
            "message": "대화 생성 성공",
            "data": {
                "response": response,
                "tts_audio": tts_audio_base64  # Base64 문자열로 반환
            },
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"대화 생성 중 오류 발생: {str(e)}")

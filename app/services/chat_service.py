import asyncio
import base64
import io
import json
from http.client import HTTPException
from fastapi import Depends
from sqlalchemy.orm import Session
from app.config.constants import CHARACTER_TTS_MAP
from app.config.elevenlabs.text_to_speech_stream import text_to_speech_data
from app.config.openAI.openai_service import get_gpt_response_limited, get_grammar_feedback, transcribe_audio
from app.database.session import get_mongo_db
from app.models.chat import Chat
from app.schemas.chat import ChatRoomCreateRequest, Chatroomresponse
from datetime import datetime
from pymongo.database import Database
def get_chatrooms(user_id: int, db: Session, skip: int = 0, limit: int = 100):
    chatrooms = db.query(Chat).filter(Chat.user_id == user_id).offset(skip).limit(limit).all()
    return [
        Chatroomresponse(
            chat_id=chatroom.chat_id,
            user_id=chatroom.user_id,
            score=chatroom.score,
            subject=chatroom.subject,
            character_name=chatroom.character_name,
            tts_id=chatroom.tts_id,
            created_at=chatroom.created_at,
            updated_at=chatroom.updated_at
        )
        for chatroom in chatrooms
    ]

def delete_chat(chat: Chat, mdb:Database, db: Session):
        db.delete(chat)
        db.commit()
        mdb["chats"].delete_one(
            {"chat_id": chat.chat_id}  # 조건: chat_id가 일치하는 문서
        )
def get_chat(user_id: int, chat_id: int, db: Session):
    return db.query(Chat).filter_by(user_id=user_id, chat_id=chat_id).first()

def get_chat_history(chat_id:int, mdb: Database):
    return mdb["chats"].find_one({"chat_id": chat_id})

def create_chatroom(req: ChatRoomCreateRequest, user_id: int, db: Session):
    tts_id = CHARACTER_TTS_MAP.get(req.character_name)
    if not tts_id:
        raise HTTPException(status_code=400, detail="유효하지 않은 캐릭터 이름입니다.")
    new_chat = Chat(
        user_id=user_id,
        subject=req.subject,
        character_name=req.character_name,
        tts_id=tts_id,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    db.add(new_chat)
    db.commit()
    db.refresh(new_chat)
    return new_chat

def create_chatroom_mongo(chat, mdb:Database):
    mdb["chats"].insert_one({"chat_id": chat.chat_id, "messages":[]})


async def event_generator(chat_id: int, tts_id:str,file_content_io: io.BytesIO, filename:str,mdb: Database = Depends(get_mongo_db)):
    try:
        transcription = await transcribe_audio(file_content_io,filename)
        yield f"data: {json.dumps({'step': 'transcription', 'content': str(transcription)})}\n\n"
        await asyncio.sleep(0.1)
    except Exception as e:
        yield f"data: {json.dumps({'step': 'error', 'message': f'STT 변환 실패: {str(e)}'})}\n\n"
        return

    try:
        gpt_response_full = ""
        gpt_response = get_gpt_response_limited(chat_id=chat_id, prompt=transcription, mdb=mdb)

        async for chunk in gpt_response:
            gpt_response_full += chunk
            yield f"data: {json.dumps({'step': 'gpt_response', 'content': chunk})}\n\n"
            await asyncio.sleep(0.1)

        tts_audio = text_to_speech_data(text=gpt_response_full, voice_id=tts_id)
        tts_audio.seek(0)
        tts_audio_base64 = base64.b64encode(tts_audio.getvalue()).decode("utf-8")
        yield f"data: {json.dumps({'step': 'tts_audio', 'content': tts_audio_base64})}\n\n"
        await asyncio.sleep(0.1)

        grammar_feedback = await get_grammar_feedback(prompt=transcription)
        yield f"data: {json.dumps({'step': 'grammar_feedback', 'content': grammar_feedback})}\n\n"
        await asyncio.sleep(0.1)


        user_bubble = {
            "role": "user",
            "content": transcription,
            "grammar_feedback": grammar_feedback,
        }

        gpt_bubble = {
            "role": "assistant",
            "content": gpt_response_full,
        }

        mdb["chats"].update_one(
            {"chat_id": chat_id},
            {"$push": {
                "messages": {
                    "$each": [user_bubble, gpt_bubble]
                }
            }},
            upsert=True
        )

    except Exception as e:
        yield f"data: {json.dumps({'step': 'error', 'message': f'오류 발생: {str(e)}'})}\n\n"
        return
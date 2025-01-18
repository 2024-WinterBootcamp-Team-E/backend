import asyncio
import base64
import io
import json
from http.client import HTTPException
from fastapi import Depends
from sqlalchemy.orm import Session
from app.config.constants import CHARACTER_TTS_MAP
from app.config.elevenlabs.text_to_speech_stream import text_to_speech_stream
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


async def event_generator(chat_id: int, tts_id: str, file_content_io: io.BytesIO, filename: str, mdb: Database = Depends(get_mongo_db)):
    try:
        # Step 1: Transcription
        transcription = await generate_transcription(file_content_io, filename)
        yield f"data: {json.dumps({'step': 'transcription', 'content': transcription})}\n\n"

        # Step 2: GPT Response
        gpt_response_full = ""
        async for chunk in generate_gpt_response(chat_id, transcription, mdb):
            gpt_response_full += chunk
            yield f"data: {json.dumps({'step': 'gpt_response', 'content': chunk})}\n\n"

        # Step 3: TTS Audio
        tts_audio_base64 = generate_tts_audio(gpt_response_full, tts_id)
        yield f"data: {json.dumps({'step': 'tts_audio', 'content': tts_audio_base64})}\n\n"

        # Step 4: Grammar Feedback
        grammar_feedback = await generate_grammar_feedback(transcription)
        yield f"data: {json.dumps({'step': 'grammar_feedback', 'content': grammar_feedback})}\n\n"

        # Step 5: Save to Database
        save_to_database(chat_id, transcription, gpt_response_full, grammar_feedback, mdb)

    except HTTPException as e:
        yield f"data: {json.dumps({'step': 'error', 'message': e.detail})}\n\n"


async def generate_transcription(file_content_io: io.BytesIO, filename: str) -> str:
    try:
        transcription = await transcribe_audio(file_content_io, filename)
        return transcription
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"STT 변환 실패: {str(e)}")


async def generate_gpt_response(chat_id: int, transcription: str, mdb: Database) -> str:
    try:
        gpt_response_full = ""
        gpt_response = get_gpt_response_limited(chat_id=chat_id, prompt=transcription, mdb=mdb)
        async for chunk in gpt_response:
            gpt_response_full += chunk
            yield chunk
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GPT 응답 생성 실패: {str(e)}")


def generate_tts_audio(gpt_response_full: str, tts_id: str) -> str:
    try:
        tts_audio = text_to_speech_stream(text=gpt_response_full, voice_id=tts_id)
        tts_audio.seek(0)
        return base64.b64encode(tts_audio.getvalue()).decode("utf-8")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS 변환 실패: {str(e)}")


async def generate_grammar_feedback(transcription: str) -> str:
    try:
        return await get_grammar_feedback(prompt=transcription)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"문법 피드백 생성 실패: {str(e)}")


def save_to_database(chat_id: int, transcription: str, gpt_response_full: str, grammar_feedback: str, mdb: Database):
    print(f'grammar_feed')
    user_bubble = {
        "role": "user",
        "content": transcription,
        "grammar_feedback": grammar_feedback,
    }

    gpt_bubble = {
        "role": "assistant",
        "content": gpt_response_full,
    }

    try:
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
        raise HTTPException(status_code=500, detail=f"데이터베이스 저장 실패: {str(e)}")
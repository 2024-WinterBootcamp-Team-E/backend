import asyncio
import base64
import io,re
import json
import uuid

from fastapi import HTTPException
from fastapi import Depends
from sqlalchemy.orm import Session
from app.config.constants import CHARACTER_TTS_MAP
from app.config.elevenlabs.text_to_speech_stream import generate_tts_audio_async
from app.config.openAI.openai_service import get_gpt_response_limited, get_grammar_feedback, transcribe_audio
from app.database.session import get_mongo_db
from app.models.chat import Chat
from app.schemas.chat import ChatRoomCreateRequest, Chatroomresponse
from pymongo.database import Database

def get_chatrooms(user_id: int, db: Session, skip: int = 0, limit: int = 100):
    chatrooms = db.query(Chat).filter(Chat.user_id == user_id).offset(skip).limit(limit).all()
    return [
        Chatroomresponse(
            chat_id=chatroom.chat_id,
            title=chatroom.title,
            character_name=chatroom.character_name,
            updated_at=chatroom.updated_at
        )
        for chatroom in chatrooms
    ]

def delete_chat(chat: Chat, mdb:Database, db: Session):
        db.delete(chat)
        db.commit()
        mdb["chats"].delete_one(
            {"chat_id": chat.chat_id}
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
        title=req.title,
        character_name=req.character_name,
        tts_id=tts_id,
    )
    db.add(new_chat)
    db.commit()
    db.refresh(new_chat)
    new_chat = Chatroomresponse(
        chat_id=new_chat.chat_id,
        title=new_chat.title,
        character_name=new_chat.character_name,
        updated_at=new_chat.updated_at
    )
    return new_chat

def create_chatroom_mongo(chat, mdb:Database):
    mdb["chats"].insert_one({"chat_id": chat.chat_id, "messages":[]})

# 음성을 텍스트로 변환, GPT 응답, 음성 변환, 문법 피드백을 처리, 결과를 실시간 전달
async def event_generator(chat_id: int, tts_id: str, file_content_io: io.BytesIO, filename: str, title:str, country:str, mdb: Database = Depends(get_mongo_db)):
    try:
        transcription = await generate_transcription(file_content_io, filename)
        yield f"data: {json.dumps({'step': 'transcription', 'content': transcription})}\n\n"

        send_queue = asyncio.Queue()

        async def process_gpt_and_tts() -> str:
            gpt_response_full = ""
            buffer = ""
            sentence_end_pattern = re.compile(r'([.!?])')

            async for gpt_chunk in generate_gpt_response(chat_id, transcription, title, country, mdb):
                gpt_response_full += gpt_chunk
                buffer += gpt_chunk
                await send_queue.put(
                    json.dumps({'step': 'gpt_response', 'content': gpt_chunk})
                )
                sentences = []
                while True:
                    match = sentence_end_pattern.search(buffer)
                    if match:
                        end_idx = match.end()
                        sentence = buffer[:end_idx].strip()
                        if sentence:
                            sentences.append(sentence)
                        buffer = buffer[end_idx:].strip()
                    else:
                        break
                for sentence in sentences:
                    sentence_id = str(uuid.uuid4())
                    try:
                        tts_response = await generate_tts_audio_async(sentence, tts_id)
                        tts_content = base64.b64encode(tts_response).decode('utf-8')
                        await send_queue.put(
                            json.dumps({
                                'step': 'tts_audio',
                                'sentence_id': sentence_id,
                                'content': tts_content
                            })
                        )
                    except Exception as e:
                        await send_queue.put(
                            json.dumps({'step': 'error', 'message': f'TTS Error: {str(e)}'})
                        )

            if buffer:
                sentence_id = str(uuid.uuid4())
                try:
                    tts_response = await generate_tts_audio_async(buffer, tts_id)
                    tts_content = base64.b64encode(tts_response).decode('utf-8')
                    await send_queue.put(
                        json.dumps({
                            'step': 'tts_audio',
                            'sentence_id': sentence_id,
                            'content': tts_content
                        })
                    )
                except Exception as e:
                    await send_queue.put(
                        json.dumps({'step': 'error', 'message': f'TTS Error: {str(e)}'})
                    )

            await send_queue.put(None)
            return gpt_response_full

        gpt_tts_task = asyncio.create_task(process_gpt_and_tts())
        grammar_task = asyncio.create_task(generate_grammar_feedback(transcription, country))

        while True:
            try:
                message = await asyncio.wait_for(send_queue.get(), timeout=10.0)
                if message is None:  #
                    break
                yield f"data: {message}\n\n"
            except asyncio.TimeoutError:
                yield f"data: {json.dumps({'step': 'error', 'message': 'Timeout occurred while processing data'})}\n\n"
                break

        gpt_response_full = await gpt_tts_task

        grammar_feedback = await grammar_task
        yield f"data: {json.dumps({'step': 'grammar_feedback', 'content': grammar_feedback})}\n\n"
        save_to_database(chat_id, transcription, gpt_response_full, grammar_feedback, mdb)
    except HTTPException as e:
        yield f"data: {json.dumps({'step': 'error', 'message': e.detail})}\n\n"

async def generate_transcription(file_content_io: io.BytesIO, filename: str) -> str:
    try:
        transcription = await transcribe_audio(file_content_io, filename)
        return transcription
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"STT 변환 실패: {str(e)}")

async def generate_gpt_response(chat_id: int, transcription: str, title:str, country:str, mdb: Database) -> str:
    try:
        gpt_response_full = ""
        gpt_response = get_gpt_response_limited(chat_id=chat_id, prompt=transcription, title=title, country=country, mdb=mdb)
        async for chunk in gpt_response:
            gpt_response_full += chunk
            yield chunk
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GPT 응답 생성 실패: {str(e)}")

async def generate_grammar_feedback(transcription: str, country:str) -> str:
    try:
        return await get_grammar_feedback(prompt=transcription, country=country)
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
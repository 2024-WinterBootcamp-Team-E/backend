import asyncio
import base64
import io
import json
from fastapi import HTTPException
from fastapi import Depends
from sqlalchemy.orm import Session
from app.config.constants import CHARACTER_TTS_MAP
from app.config.elevenlabs.text_to_speech_stream import generate_tts_audio_async
from app.config.openAI.openai_service import get_gpt_response_limited, get_grammar_feedback, transcribe_audio
from app.database.session import get_mongo_db, get_db
from app.models.chat import Chat
from app.schemas.chat import ChatRoomCreateRequest, Chatroomresponse
from datetime import datetime
from pymongo.database import Database
def get_chatrooms(user_id: int, db: Session, skip: int = 0, limit: int = 100):
    chatrooms = db.query(Chat).filter(Chat.user_id == user_id).offset(skip).limit(limit).all()
    return [
        Chatroomresponse(
            chat_id=chatroom.chat_id,
            #user_id=chatroom.user_id,
            #score=chatroom.score,
            title=chatroom.title,
            character_name=chatroom.character_name,
            #tts_id=chatroom.tts_id,
            #created_at=chatroom.created_at,
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


async def event_generator(chat_id: int, tts_id: str, file_content_io: io.BytesIO, filename: str, title:str, country:str, mdb: Database = Depends(get_mongo_db)):
    try:
        # Step 1: Transcription
        transcription = await generate_transcription(file_content_io, filename)
        yield f"data: {json.dumps({'step': 'transcription', 'content': transcription})}\n\n"

        # Step 2: Queue를 사용하여 GPT와 TTS 작업 병렬 실행
        send_queue = asyncio.Queue()

        async def process_gpt_and_tts():
            gpt_response_full = ""
            buffer = ""  # GPT 청크를 버퍼링
            async for gpt_chunk in generate_gpt_response(chat_id, transcription, title, country, mdb):
                gpt_response_full += gpt_chunk
                buffer += gpt_chunk

                # 버퍼가 일정 길이를 넘으면 TTS 요청
                if len(buffer) > 50 or "." in buffer:
                    # GPT 청크를 Queue에 추가
                    await send_queue.put(
                        json.dumps({'step': 'gpt_response', 'content': buffer})
                    )

                    # TTS 요청
                    async for tts_chunk in generate_tts_audio_async(buffer, tts_id):
                        await send_queue.put(
                            json.dumps({'step': 'tts_audio', 'content': base64.b64encode(tts_chunk).decode('utf-8')})
                        )
                    buffer = ""  # 버퍼 초기화

            # 남아있는 버퍼 처리
            if buffer:
                await send_queue.put(
                    json.dumps({'step': 'gpt_response', 'content': buffer})
                )
                async for tts_chunk in generate_tts_audio_async(buffer, tts_id):
                    await send_queue.put(
                        json.dumps({'step': 'tts_audio', 'content': base64.b64encode(tts_chunk).decode('utf-8')})
                    )

            await send_queue.put(None)  # 작업 종료 신호
            return gpt_response_full

        # 두 작업을 병렬로 실행
        gpt_tts_task = asyncio.create_task(process_gpt_and_tts())
        grammar_task = asyncio.create_task(generate_grammar_feedback(transcription, country))

        # Queue에서 데이터를 클라이언트로 전송
        while True:
            try:
                message = await asyncio.wait_for(send_queue.get(), timeout=2.0)
                if message is None:  # 작업 종료
                    break
                yield f"data: {message}\n\n"
            except asyncio.TimeoutError:
                yield f"data: {json.dumps({'step': 'error', 'message': 'Timeout occurred while processing data'})}\n\n"
                break

        # GPT와 TTS 작업 완료 대기
        gpt_response_full = await gpt_tts_task

        # Grammar 피드백 작업 완료 대기
        grammar_feedback = await grammar_task
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
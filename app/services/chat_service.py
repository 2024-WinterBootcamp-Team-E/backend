from sqlalchemy.orm import Session
from fastapi import UploadFile
from app.config.openAI.openai_service import transcribe_audio, get_gpt_response_limited, \
    get_grammar_feedback
from app.models.chat import Chat
from app.schemas.chat import ChatRoomCreateRequest
from datetime import datetime
from app.models.bubble import Bubble
from pymongo.database import Database
from fastapi import HTTPException

def get_chatrooms(user_id: int, db: Session):
    return db.query(Chat).filter(Chat.user_id == user_id).all()

def delete_chat(chat: Chat, mdb:Database, db: Session):
        db.delete(chat)
        db.commit()
        mdb["chats"].delete_one(
            {"chat_id": Chat.chat_id}  # 조건: chat_id가 일치하는 문서
        )
def get_chat(user_id: int, chat_id: int, db: Session):
    return db.query(Chat).filter_by(user_id=user_id, chat_id=chat_id).first()

def get_chat_history(chat_id:int, mdb: Database):
    return mdb["chats"].find_one({"chat_id": chat_id})

def create_chatroom(req: ChatRoomCreateRequest, user_id: int, character_id: int, db: Session):
    new_chat = Chat(
        user_id=user_id,
        character_id=character_id,
        subject=req.subject,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        is_deleted=False
    )
    db.add(new_chat)
    db.commit()
    db.refresh(new_chat)
    return new_chat

def create_chatroom_mongo(chat, mdb:Database):
    mdb["chats"].insert_one({"chat_id": chat.chat_id, "messages":[]})

def create_bubble_result(chat_id: int, transcription: str, mdb: Database, tts_id: str):
    gpt_response = get_gpt_response_limited(prompt=transcription, messages=[])
    grammar_feedback = get_grammar_feedback(prompt=transcription, messages=[])

    # 사용자 입력 Bubble 생성
    user_bubble = {
        "role" : "user",
        "content": transcription,
        "grammar_feedback": grammar_feedback,
        #"correct_sentence": correct_sentence
    }

    # GPT 응답 Bubble 생성
    gpt_bubble = {
        "role": "assistant",
        "content": gpt_response
    }

    mdb["chats"].update_one(
        {"chat_id": chat_id},  # 조건: chat_id로 문서 찾기
        {"$push": {  # messages 배열에 메시지 추가
                "messages": {
                    "$each": [user_bubble, gpt_bubble]
                }
            }
        },
        upsert=True  # 문서가 없으면 새로 생성
    )

    # 결과 반환
    return {
        "user_input": transcription,
        "gpt_response": gpt_response,
        "grammar_feedback": grammar_feedback
    }

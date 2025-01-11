from sqlalchemy.orm import Session
from fastapi import UploadFile
from app.config.openAI.openai_service import transcribe_audio, get_gpt_response
from app.models.chat import Chat
from app.schemas.chat import ChatRoomCreateRequest
from datetime import datetime
from app.models.bubble import Bubble


def get_chatrooms(user_id: int,db: Session):
    return db.query(Chat).filter(Chat.user_id == user_id).all()
def delete_chat(chat: Chat, db: Session):
        db.delete(chat)
        db.commit()
def get_chat(user_id: int, chat_id: int, db: Session):
    return db.query(Chat).filter_by(user_id=user_id, chat_id=chat_id).first()

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

def create_bubble_service(chat_id: int, transcription: str, db: Session):
    # GPT 응답 생성
    gpt_response = get_gpt_response(prompt=transcription, messages=[])

    # 문법 피드백 생성
    grammar_feedback = get_gpt_response(
        prompt=f"Correct the grammar for the following sentence: '{transcription}'",
        messages=[]
    )

    # 사용자 입력 Bubble 생성
    user_bubble = Bubble(
        chat_id=chat_id,
        content=transcription,  # 사용자의 입력
        speaker=0,  # 사용자
        grammar_feedback=None,  # 사용자 메시지에는 피드백 없음
        created_at=datetime.now()
    )

    # GPT 응답 Bubble 생성
    gpt_bubble = Bubble(
        chat_id=chat_id,
        content=gpt_response,  # GPT의 응답
        speaker=1,  # GPT
        grammar_feedback=grammar_feedback,  # 문법 피드백
        created_at=datetime.now()
    )

    # DB에 Bubble 저장
    db.add_all([user_bubble, gpt_bubble])
    db.commit()

    # 결과 반환
    return {
        "user_input": transcription,
        "gpt_response": gpt_response,
        "grammar_feedback": grammar_feedback
    }

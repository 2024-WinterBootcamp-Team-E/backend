from sqlalchemy.orm import Session
from app.models.chat import Chat
from app.schemas.chat import ChatRoomCreateRequest
from datetime import datetime


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
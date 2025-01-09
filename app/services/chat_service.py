from sqlalchemy.orm import Session
from app.models.chat import Chat


def get_chatrooms(user_id: int,db: Session):
    return db.query(Chat).filter(Chat.user_id == user_id).all()

def delete_chat(chat: Chat, db: Session):
        db.delete(chat)
        db.commit()

def get_chat(user_id: int, chat_id: int, db: Session):
    return db.query(Chat).filter_by(user_id=user_id, chat_id=chat_id).first()

from sqlalchemy.orm import Session
from app.models.character import Character


def get_character(db: Session):
    return db.query(Character).all()



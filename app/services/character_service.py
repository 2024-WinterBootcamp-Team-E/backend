# from sqlalchemy.orm import Session
# from app.models.character import Character
#
#
# def get_characters(db: Session):
#     return db.query(Character).all()
#
#
# def get_character_by_name(db: Session, character_name: str) -> Character:
#     return db.query(Character).filter(Character.name == character_name).first()

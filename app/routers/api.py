from fastapi import APIRouter
from . import users, chat, sentence, character

router = APIRouter(
    prefix="/api/v1"
)

router.include_router(users.router)  
router.include_router(chat.router)  
router.include_router(sentence.router) 
router.include_router(character.router)
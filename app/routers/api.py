from fastapi import APIRouter
from . import users, chat, sentence, character, feedback

router = APIRouter(
    prefix="/api/v1"
)

router.include_router(users.router)  
router.include_router(chat.router)  
router.include_router(sentence.router) 
router.include_router(character.router)
router.include_router(feedback.router)
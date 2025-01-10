from fastapi import APIRouter
from . import users, chat, sentence, character

router = APIRouter(
    prefix="/api/v1"  # 모든 엔드포인트에 /api/v1 추가
)

router.include_router(users.router)  # users 라우트를 포함
router.include_router(chat.router)  # chat 라우터를 포함
router.include_router(sentence.router)  # Sentence 라우터를 포함
router.include_router(character.router)  # character 라우터를 포함
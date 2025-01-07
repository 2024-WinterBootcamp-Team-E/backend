from fastapi import APIRouter
from . import users

router = APIRouter(
    prefix="/api/v1"  # 모든 엔드포인트에 /api/v1 추가
)

router.include_router(users.router)  # users 라우트를 포함

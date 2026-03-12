from fastapi import APIRouter

from app.api.v1.ai import router as ai_router
from app.api.v1.auth import router as auth_router
from app.api.v1.backtest import router as backtest_router
from app.api.v1.market import router as market_router
from app.api.v1.oauth import router as oauth_router
from app.api.v1.users import router as users_router

v1_router = APIRouter()


@v1_router.get("/")
async def v1_root() -> dict[str, str]:
    return {"message": "FinVest Platform API v1"}


v1_router.include_router(ai_router)
v1_router.include_router(auth_router)
v1_router.include_router(backtest_router)
v1_router.include_router(market_router)
v1_router.include_router(oauth_router)
v1_router.include_router(users_router)

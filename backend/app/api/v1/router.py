from fastapi import APIRouter

v1_router = APIRouter()


@v1_router.get("/")
async def v1_root() -> dict[str, str]:
    return {"message": "FinVest Platform API v1"}

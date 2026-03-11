"""FinVest Platform API - Main application."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api.v1.router import v1_router
from app.config import settings
from app.core.redis import close_redis, get_redis
from app.db.session import engine

# Initialize Sentry (no-op if DSN is empty)
if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        traces_sample_rate=0.1,
        environment="development" if settings.DEBUG else "production",
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Startup
    redis = await get_redis()
    await redis.ping()
    yield
    # Shutdown
    await close_redis()
    await engine.dispose()


app = FastAPI(
    title="FinVest Platform API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting (disabled when TESTING=true)
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"], enabled=not settings.TESTING)
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(status_code=429, content={"detail": "Too many requests"})


# Prometheus metrics (exposes /metrics endpoint)
Instrumentator().instrument(app).expose(app, include_in_schema=False)

app.include_router(v1_router, prefix="/api/v1")


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}

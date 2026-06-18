import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy.ext.asyncio import AsyncEngine

from app.api.v1.routers.auth import router as auth_2fa_router
from app.api.v1.routers.auth_session import router as auth_session_router
from app.api.v1.routers.health import router as health_router
from app.api.v1.routers.password_reset import router as password_reset_router
from app.core.dependencies import get_engine, get_settings
from app.core.logging import setup_json_logging
from app.core.observability import setup_observability
from app.core.rate_limit import limiter


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()
    setup_json_logging()
    setup_observability(app, settings)
    yield
    engine: AsyncEngine = get_engine()
    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(title="activia-trace", version="0.1.0", lifespan=lifespan)

    # Rate limiter (SlowAPI)
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # Routers
    app.include_router(health_router)
    app.include_router(auth_session_router)
    app.include_router(auth_2fa_router)
    app.include_router(password_reset_router)
    return app


app = create_app()

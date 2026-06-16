import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncEngine

from app.api.v1.routers.health import router as health_router
from app.core.dependencies import get_engine, get_settings
from app.core.logging import setup_json_logging
from app.core.observability import setup_observability


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
    app.include_router(health_router)
    return app


app = create_app()

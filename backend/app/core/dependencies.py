from collections.abc import AsyncGenerator
from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.core.config import Settings
from app.core.database import create_engine, create_session_factory


@lru_cache
def get_settings() -> Settings:
    return Settings()


def get_engine() -> AsyncEngine:
    return create_engine(get_settings())


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    return create_session_factory(get_engine())


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    factory = get_session_factory()
    session = factory()
    try:
        yield session
    finally:
        await session.close()

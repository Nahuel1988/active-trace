from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import Settings


class Base(DeclarativeBase):
    pass


def create_engine(settings: Settings):
    return create_async_engine(
        settings.database_url,
        pool_pre_ping=True,
        echo=False,
    )


def create_test_engine(database_url: str):
    return create_async_engine(
        database_url,
        pool_pre_ping=True,
        echo=False,
    )


def create_session_factory(engine):
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

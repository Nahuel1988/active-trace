from sqlalchemy import NullPool
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


def create_test_engine(database_url: str, **kwargs):
    """Crea engine asíncrono para tests con NullPool.

    NullPool evita que las conexiones se reutilicen entre event loops
    distintos (pytest-asyncio crea un loop por test en scope function).
    En Windows con IocpProactor, asyncpg liga cada conexión al loop
    que la creó, causando "Event loop is closed" si se reusa.
    """
    return create_async_engine(
        database_url,
        poolclass=NullPool,
        echo=False,
        **kwargs,
    )


def create_session_factory(engine):
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

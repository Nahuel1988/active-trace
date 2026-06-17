import os
import uuid
from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.database import create_test_engine, create_session_factory


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--run-db",
        action="store_true",
        default=False,
        help="run tests that require a real PostgreSQL database",
    )


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "requires_db: test requires a real PostgreSQL database")
    config.addinivalue_line("markers", "slow: test is slow")


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if config.getoption("--run-db"):
        return
    skip_db = pytest.mark.skip(reason="need --run-db option to run (requires PostgreSQL)")
    for item in items:
        if "requires_db" in item.keywords:
            item.add_marker(skip_db)


@pytest.fixture(scope="session", autouse=True)
def _set_env() -> None:
    test_env = Path(__file__).resolve().parent.parent / ".env.test"
    if test_env.exists():
        for line in test_env.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ.setdefault(key.strip(), val.strip().strip("\"'"))


@pytest.fixture(scope="session")
def settings() -> Settings:
    return Settings()


@pytest.fixture(scope="session")
def db_engine(settings: Settings):
    url = settings.test_database_url or settings.database_url
    return create_test_engine(url)


@pytest.fixture(scope="function")
async def db_session(db_engine) -> AsyncSession:
    factory = create_session_factory(db_engine)
    session = factory()
    try:
        yield session
    finally:
        await session.close()


@pytest.fixture(scope="function")
async def tenant_factory(db_session: AsyncSession):
    """Fixture que crea un Tenant de prueba y retorna una factory function.

    Uso:
        tenant = await tenant_factory(db_session, slug="mi-slug")
    """

    async def _make_tenant(
        session: AsyncSession | None = None,
        slug: str | None = None,
        nombre: str = "Test Tenant",
    ) -> "Tenant":
        from app.models.tenant import Tenant

        sess = session or db_session
        t = Tenant(
            id=uuid.uuid4(),
            slug=slug or f"test-{uuid.uuid4().hex[:8]}",
            nombre=nombre,
            activo=True,
        )
        sess.add(t)
        await sess.commit()
        await sess.refresh(t)
        return t

    return _make_tenant

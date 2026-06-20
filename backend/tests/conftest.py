import asyncio
import os
import sys
import uuid
from pathlib import Path

# ── Windows + asyncpg fix ──────────────────────────────────────────────────
# asyncpg requires SelectorEventLoop (no ProactorEventLoop) for socket
# operations. Python 3.8+ defaults to ProactorEventLoop on Windows.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.database import create_test_engine, create_session_factory

# ---------------------------------------------------------------------------
# Cargar .env.test a nivel de módulo (ANTES de cualquier fixture o import).
# Esto es necesario porque app.core.security.encryption_service evalúa
# Settings() en tiempo de importación (singleton module-level), y un fixture
# session-scoped corre después de la colección de tests.
# ---------------------------------------------------------------------------
_test_env = Path(__file__).resolve().parent.parent / ".env.test"
if _test_env.exists():
    for _line in _test_env.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _key, _val = _line.split("=", 1)
            os.environ.setdefault(_key.strip(), _val.strip().strip("\"'"))

del _test_env


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


@pytest.fixture(scope="session")
def settings() -> Settings:
    return Settings()


@pytest.fixture(scope="session")
async def db_engine(settings: Settings):
    """Engine async session-scoped.

    Debe ser async para que asyncpg cree las conexiones TCP dentro del mismo
    event loop que usarán los tests. En Windows con IocpProactor, un engine
    creado fuera del event loop no puede conectarse a Docker via asyncpg
    (WinError 64 / ConnectionResetError).
    """
    import app.models  # noqa: F401 — registra todos los modelos en Base.metadata

    from app.core.database import Base

    url = settings.test_database_url or settings.database_url
    engine = create_test_engine(url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture(scope="session")
async def create_test_schema(db_engine):
    """Fixture de compatibilidad: el schema ya fue creado por db_engine."""
    yield


@pytest.fixture(scope="function")
async def db_session(db_engine) -> AsyncSession:
    factory = create_session_factory(db_engine)
    session = factory()
    try:
        yield session
    finally:
        await session.close()


@pytest.fixture(scope="function")
async def materia(db_session, tenant_factory):
    t = await tenant_factory(db_session)
    from app.models.materia import Materia

    m = Materia(id=uuid.uuid4(), tenant_id=t.id, codigo="M01", nombre="Matemática")
    db_session.add(m)
    await db_session.commit()
    await db_session.refresh(m)
    return t, m


@pytest.fixture(scope="function")
async def cohorte(db_session, materia):
    t, m = materia
    from app.models.carrera import Carrera, EstadoCarrera
    from app.models.cohorte import Cohorte

    car = Carrera(
        id=uuid.uuid4(),
        tenant_id=t.id,
        codigo="CAR01",
        nombre="Ingeniería",
        estado=EstadoCarrera.Activa,
    )
    db_session.add(car)
    await db_session.flush()

    c = Cohorte(
        id=uuid.uuid4(),
        tenant_id=t.id,
        carrera_id=car.id,
        nombre="2025",
        anio=2025,
        vig_desde="2025-01-01",
        vig_hasta="2025-12-31",
    )
    db_session.add(c)
    await db_session.commit()
    await db_session.refresh(c)
    return t, m, c


@pytest.fixture(scope="function")
async def user_factory(db_session: AsyncSession):
    """Fixture que crea un User de prueba y retorna la factory function.

    Uso:
        user = await user_factory(db_session, tenant_id=t.id)
    """

    async def _make_user(
        session: AsyncSession | None = None,
        tenant_id: uuid.UUID | None = None,
        email: str = "test@example.com",
    ) -> "User":
        from app.core.security import encryption_service, email_lookup_hash
        from app.models.user import User

        sess = session or db_session
        u = User(
            id=uuid.uuid4(),
            tenant_id=tenant_id or uuid.uuid4(),
            email_encrypted=encryption_service.encrypt(email),
            email_lookup=email_lookup_hash(email),
            password_hash="$argon2id$test",
            legajo=f"LEG-{uuid.uuid4().hex[:8]}",
            is_active=True,
        )
        sess.add(u)
        await sess.commit()
        await sess.refresh(u)
        return u

    return _make_user


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

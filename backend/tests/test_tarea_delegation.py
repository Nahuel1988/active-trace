"""Tests de delegación de tareas (C-16, spec: tarea-delegation).

RED → GREEN → TRIANGULATE → REFACTOR.
Requiere PostgreSQL (--run-db).
"""

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.dependencies import get_current_user
from app.core.permissions import PermissionGrant
from app.main import create_app

pytestmark = pytest.mark.requires_db


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def app(db_engine):  # db_engine asegura que las tablas existen
    import os

    from app.core.dependencies import get_settings

    # Redirigir la app a la BD de test para que encuentre las tablas que
    # crea db_engine (session-scoped en conftest.py).
    test_url = os.environ.get("TEST_DATABASE_URL")
    if test_url:
        os.environ["DATABASE_URL"] = test_url
        get_settings.cache_clear()
    return create_app()


@pytest.fixture
async def _mock_user(db_session):
    """Creates a real Tenant + User in the DB and returns a MagicMock with real IDs."""
    from unittest.mock import MagicMock

    from app.models.tenant import Tenant
    from app.models.user import User

    tenant = Tenant(
        id=uuid.uuid4(),
        slug=f"test-{uuid.uuid4().hex[:8]}",
        nombre="Test Tenant",
    )
    db_session.add(tenant)

    user = User(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        email_encrypted="test@test.com",
        email_lookup=f"test-{uuid.uuid4().hex[:16]}",
        password_hash="$argon2id$v=19$m=65536,t=3,p=4$test",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    mock = MagicMock()
    mock.id = user.id
    mock.actor_id = user.id
    mock.tenant_id = tenant.id
    mock.impersonated = False
    return mock


@pytest.fixture
async def _mock_user_b(_mock_user, db_session):
    """Second real user in the same tenant (for delegation targets)."""
    from unittest.mock import MagicMock

    from app.models.user import User

    user = User(
        id=uuid.uuid4(),
        tenant_id=_mock_user.tenant_id,
        email_encrypted="test_b@test.com",
        email_lookup=f"test-b-{uuid.uuid4().hex[:16]}",
        password_hash="$argon2id$v=19$m=65536,t=3,p=4$test",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    mock = MagicMock()
    mock.id = user.id
    mock.actor_id = user.id
    mock.tenant_id = user.tenant_id
    mock.impersonated = False
    return mock


@pytest.fixture
async def client_profesor(app, _mock_user):
    """PROFESOR = scope 'propio'."""
    app.dependency_overrides[get_current_user] = lambda: _mock_user
    grant = PermissionGrant(code="tareas:gestionar", scope="propio")
    transport = ASGITransport(app=app)
    with patch(
        "app.services.permission_service.PermissionService.verify_permission",
        new=AsyncMock(return_value=grant),
    ):
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
    app.dependency_overrides.clear()


@pytest.fixture
async def client_coordinador(app, _mock_user):
    """COORDINADOR = scope 'global'."""
    app.dependency_overrides[get_current_user] = lambda: _mock_user
    grant = PermissionGrant(code="tareas:gestionar", scope="global")
    transport = ASGITransport(app=app)
    with patch(
        "app.services.permission_service.PermissionService.verify_permission",
        new=AsyncMock(return_value=grant),
    ):
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Tests — Delegación
# ---------------------------------------------------------------------------


class TestTareaDelegacion:
    """Scenario: delegar una tarea a otro docente."""

    async def test_01_delegar_ok(self, client_coordinador, _mock_user, _mock_user_b):
        """RED: POST /api/tareas/{id}/asignar → 200, asignado_a actualizado."""
        resp = await client_coordinador.post(
            "/api/tareas",
            json={"asignado_a": str(_mock_user.id), "descripcion": "Deleg test"},
        )
        tarea_id = resp.json()["id"]

        delegar_resp = await client_coordinador.post(
            f"/api/tareas/{tarea_id}/asignar",
            json={"asignado_a": str(_mock_user_b.id)},
        )
        assert delegar_resp.status_code == 200
        data = delegar_resp.json()
        assert data["asignado_a"] == str(_mock_user_b.id)

    async def test_02_delegar_conserva_trazabilidad(self, client_coordinador, _mock_user, _mock_user_b):
        """TRIANG: asignado_por = quien delegó (el de la sesión)."""
        resp = await client_coordinador.post(
            "/api/tareas",
            json={"asignado_a": str(_mock_user.id), "descripcion": "Trace test"},
        )
        tarea_id = resp.json()["id"]

        # Delegar
        delegar_resp = await client_coordinador.post(
            f"/api/tareas/{tarea_id}/asignar",
            json={"asignado_a": str(_mock_user_b.id)},
        )
        data = delegar_resp.json()
        assert data["asignado_a"] == str(_mock_user_b.id)
        assert data["asignado_por"] == str(_mock_user.id)

    async def test_03_delegar_otro_tenant_400(self, client_coordinador, _mock_user):
        """TRIANG: delegar a user de otro tenant → 400."""
        resp = await client_coordinador.post(
            "/api/tareas",
            json={"asignado_a": str(_mock_user.id), "descripcion": "Cross tenant"},
        )
        tarea_id = resp.json()["id"]

        # Simular otro tenant cambiando tenant_id del mock
        # La validación se hace contra user_repo, que busca el id en el tenant actual
        otro_tenant_user = uuid.uuid4()

        delegar_resp = await client_coordinador.post(
            f"/api/tareas/{tarea_id}/asignar",
            json={"asignado_a": str(otro_tenant_user)},
        )
        # 400 porque el user no existe en el tenant del mock
        assert delegar_resp.status_code == 400

    async def test_04_profesor_delega_propia_ok(self, client_profesor, _mock_user, _mock_user_b):
        """TRIANG: PROFESOR delega tarea donde es asignado_a → 200."""
        resp = await client_profesor.post(
            "/api/tareas",
            json={"asignado_a": str(_mock_user.id), "descripcion": "Prof own"},
        )
        tarea_id = resp.json()["id"]

        delegar_resp = await client_profesor.post(
            f"/api/tareas/{tarea_id}/asignar",
            json={"asignado_a": str(_mock_user_b.id)},
        )
        assert delegar_resp.status_code == 200

    async def test_05_profesor_delega_ajena_404(self, client_profesor, _mock_user, _mock_user_b):
        """TRIANG: PROFESOR delega tarea ajena → 404."""
        # Crear tarea para user_b (asignado_a = user_b, asignado_por = mock_user)
        resp = await client_profesor.post(
            "/api/tareas",
            json={"asignado_a": str(_mock_user_b.id), "descripcion": "Not yours"},
        )
        tarea_id = resp.json()["id"]

        # Cambiar mock para que no sea el asignado_a ni asignado_por
        _mock_user.id = uuid.uuid4()
        _mock_user.actor_id = _mock_user.id

        delegar_resp = await client_profesor.post(
            f"/api/tareas/{tarea_id}/asignar",
            json={"asignado_a": str(uuid.uuid4())},
        )
        assert delegar_resp.status_code == 404

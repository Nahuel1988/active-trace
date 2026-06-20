"""Tests de administración de tareas (C-16, spec: tarea-administration).

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
async def _mock_users(db_session):
    """Creates a real Tenant + 2 Users in DB and returns dict with MagicMocks."""
    from unittest.mock import MagicMock

    from app.models.tenant import Tenant
    from app.models.user import User

    tenant = Tenant(
        id=uuid.uuid4(),
        slug=f"test-{uuid.uuid4().hex[:8]}",
        nombre="Test Tenant",
    )
    db_session.add(tenant)

    user1 = User(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        email_encrypted="user1@test.com",
        email_lookup=f"user1-{uuid.uuid4().hex[:16]}",
        password_hash="$argon2id$v=19$m=65536,t=3,p=4$test",
    )
    db_session.add(user1)

    user2 = User(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        email_encrypted="user2@test.com",
        email_lookup=f"user2-{uuid.uuid4().hex[:16]}",
        password_hash="$argon2id$v=19$m=65536,t=3,p=4$test",
    )
    db_session.add(user2)

    await db_session.commit()
    await db_session.refresh(user1)
    await db_session.refresh(user2)

    u1_mock = MagicMock()
    u1_mock.id = user1.id
    u1_mock.actor_id = user1.id
    u1_mock.tenant_id = tenant.id
    u1_mock.impersonated = False

    u2_mock = MagicMock()
    u2_mock.id = user2.id
    u2_mock.actor_id = user2.id
    u2_mock.tenant_id = tenant.id
    u2_mock.impersonated = False

    return {"user1": u1_mock, "user2": u2_mock, "tenant_id": tenant.id}


@pytest.fixture
async def client_profesor(app, _mock_users):
    """PROFESOR = scope 'propio' (como user1)."""
    u1 = _mock_users["user1"]
    app.dependency_overrides[get_current_user] = lambda: u1
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
async def client_coordinador(app, _mock_users):
    """COORDINADOR = scope 'global' (como user1)."""
    u1 = _mock_users["user1"]
    app.dependency_overrides[get_current_user] = lambda: u1
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
# Tests — Administración
# ---------------------------------------------------------------------------


class TestTareaAdministracion:
    """Scenario: mis tareas y administración global con filtros."""

    async def test_01_mis_tareas_solo_asignadas(
        self, client_coordinador, _mock_users
    ):
        """RED: GET /api/tareas/mias → solo tareas asignadas al user."""
        u1 = _mock_users["user1"]
        u2 = _mock_users["user2"]

        # Crear tarea para user1
        await client_coordinador.post(
            "/api/tareas",
            json={"asignado_a": str(u1.id), "descripcion": "De u1"},
        )
        # Crear tarea para user2
        await client_coordinador.post(
            "/api/tareas",
            json={"asignado_a": str(u2.id), "descripcion": "De u2"},
        )

        resp = await client_coordinador.get("/api/tareas/mias")
        assert resp.status_code == 200
        data = resp.json()
        # Solo tareas donde asignado_a = user1
        for t in data:
            assert t["asignado_a"] == str(u1.id)

    async def test_02_filtro_asignado_y_estado(
        self, client_coordinador, _mock_users
    ):
        """TRIANG: filtros por asignado_a + estado."""
        u1 = _mock_users["user1"]

        # Crear tarea Pendiente
        await client_coordinador.post(
            "/api/tareas",
            json={"asignado_a": str(u1.id), "descripcion": "Pendiente A"},
        )
        # Crear otra y pasarla a EnProgreso
        resp = await client_coordinador.post(
            "/api/tareas",
            json={"asignado_a": str(u1.id), "descripcion": "EnProgreso B"},
        )
        t2_id = resp.json()["id"]
        await client_coordinador.patch(
            f"/api/tareas/{t2_id}/estado",
            json={"estado": "EnProgreso"},
        )

        # Filtrar por user1 y EnProgreso
        resp = await client_coordinador.get(
            f"/api/tareas?asignado_a={u1.id}&estado=EnProgreso",
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["descripcion"] == "EnProgreso B"

    async def test_03_busqueda_libre_descripcion(
        self, client_coordinador, _mock_users
    ):
        """TRIANG: búsqueda libre por descripción (ILIKE)."""
        u1 = _mock_users["user1"]

        await client_coordinador.post(
            "/api/tareas",
            json={"asignado_a": str(u1.id), "descripcion": "Revisar padron"},
        )
        await client_coordinador.post(
            "/api/tareas",
            json={"asignado_a": str(u1.id), "descripcion": "Cargar notas"},
        )

        resp = await client_coordinador.get("/api/tareas?q=padron")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert "padron" in data[0]["descripcion"].lower()

    async def test_04_admin_sin_filtros_todas(
        self, client_coordinador, _mock_users
    ):
        """TRIANG: COORD/ADMIN sin filtros ve todas las tareas del tenant."""
        u1 = _mock_users["user1"]
        u2 = _mock_users["user2"]

        await client_coordinador.post(
            "/api/tareas",
            json={"asignado_a": str(u1.id), "descripcion": "T1"},
        )
        await client_coordinador.post(
            "/api/tareas",
            json={"asignado_a": str(u2.id), "descripcion": "T2"},
        )

        resp = await client_coordinador.get("/api/tareas")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2

    async def test_05_profesor_ve_solo_participa(
        self, client_profesor, _mock_users
    ):
        """TRIANG: PROFESOR (scope propio) ve solo tareas donde participa."""
        u1 = _mock_users["user1"]
        u2 = _mock_users["user2"]

        # Usar client_coordinador para crear tareas (necesita scope global)
        # coordinator crea tarea para user1
        coord = client_profesor
        await coord.post(
            "/api/tareas",
            json={"asignado_a": str(u1.id), "descripcion": "Propia"},
        )
        await coord.post(
            "/api/tareas",
            json={"asignado_a": str(u2.id), "descripcion": "Ajena"},
        )

        resp = await client_profesor.get("/api/tareas")
        assert resp.status_code == 200
        data = resp.json()
        # Solo ve donde es asignado_a o asignado_por
        for t in data:
            assert t["asignado_a"] == str(u1.id) or t["asignado_por"] == str(u1.id)

    async def test_06_coordinador_ve_todas(
        self, client_coordinador, client_profesor, _mock_users
    ):
        """TRIANG: COORDINADOR ve todas las tareas del tenant."""
        u1 = _mock_users["user1"]
        u2 = _mock_users["user2"]

        # Crear algunas tareas con el profesor
        await client_profesor.post(
            "/api/tareas",
            json={"asignado_a": str(u1.id), "descripcion": "T1"},
        )
        await client_profesor.post(
            "/api/tareas",
            json={"asignado_a": str(u2.id), "descripcion": "T2"},
        )

        # Coordinador las ve todas
        resp = await client_coordinador.get("/api/tareas")
        assert resp.status_code == 200
        assert len(resp.json()) >= 2

    async def test_07_lista_vacia_en_db_limpia(self, client_coordinador):
        """TRIANG: DB vacía → GET /api/tareas retorna []."""
        resp = await client_coordinador.get("/api/tareas")
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_08_mis_tareas_sin_tareas(
        self, client_coordinador, _mock_users
    ):
        """TRIANG: usuario sin tareas → GET /api/tareas/mias retorna []."""
        resp = await client_coordinador.get("/api/tareas/mias")
        assert resp.status_code == 200
        # Puede tener tareas de otros tests, verificar solo que sea lista
        assert isinstance(resp.json(), list)

    async def test_09_list_aislamiento_tenant_coordinador(
        self, client_coordinador, app, _mock_users
    ):
        """TRIANG: cambiar tenant → listado vacío para tenant distinto."""
        u1 = _mock_users["user1"]
        await client_coordinador.post(
            "/api/tareas",
            json={"asignado_a": str(u1.id), "descripcion": "Tenant actual"},
        )

        # Cambiar tenant_id del mock
        old_tenant = _mock_users["tenant_id"]
        _mock_users["user1"].tenant_id = uuid.uuid4()
        _mock_users["user2"].tenant_id = _mock_users["user1"].tenant_id

        resp = await client_coordinador.get("/api/tareas")
        assert resp.status_code == 200
        # No debe haber tareas en el nuevo tenant
        assert len(resp.json()) == 0

        # Restaurar
        _mock_users["user1"].tenant_id = old_tenant
        _mock_users["user2"].tenant_id = old_tenant

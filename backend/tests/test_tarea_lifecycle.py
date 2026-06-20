"""Tests del ciclo de vida de tareas (C-16, spec: tarea-lifecycle).

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
# Fixtures compartidas
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
async def client_sin_permiso(app, _mock_user):
    """Client autenticado pero sin tareas:gestionar → espera 403."""
    app.dependency_overrides[get_current_user] = lambda: _mock_user
    transport = ASGITransport(app=app)
    with patch(
        "app.services.permission_service.PermissionService.verify_permission",
        new=AsyncMock(return_value=None),
    ):
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
    app.dependency_overrides.clear()


@pytest.fixture
async def client_profesor(app, _mock_user):
    """Client como PROFESOR (scope 'propio')."""
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
    """Client como COORDINADOR/ADMIN (scope 'global')."""
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
# Tests
# ---------------------------------------------------------------------------


class TestTareaLifecycle:
    """Scenario: ciclo de vida de una tarea (alta, lectura, borrado)."""

    async def test_01_sin_token_retorna_401(self, app):
        """WHEN no autenticado, THEN 401."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as cli:
            response = await cli.get("/api/tareas")
        assert response.status_code == 401

    async def test_02_sin_permiso_retorna_403(self, client_sin_permiso):
        """WHEN autenticado sin tareas:gestionar, THEN 403."""
        response = await client_sin_permiso.get("/api/tareas")
        assert response.status_code == 403

    async def test_03_create_tarea_ok(self, client_coordinador, _mock_user):
        """RED: POST /api/tareas → 201 con estado Pendiente."""
        response = await client_coordinador.post(
            "/api/tareas",
            json={"asignado_a": str(_mock_user.id), "descripcion": "Test task"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["estado"] == "Pendiente"
        assert data["asignado_por"] == str(_mock_user.id)
        assert data["asignado_a"] == str(_mock_user.id)
        assert data["descripcion"] == "Test task"

    async def test_04_create_tarea_asignado_por_body_rechazado(self, client_coordinador):
        """TRIANG: campo extra asignado_por en body → 422 (extra='forbid')."""
        response = await client_coordinador.post(
            "/api/tareas",
            json={
                "asignado_a": str(uuid.uuid4()),
                "descripcion": "Test",
                "asignado_por": str(uuid.uuid4()),
            },
        )
        assert response.status_code == 422

    async def test_05_create_tarea_materia_nula_ok(self, client_coordinador, _mock_user):
        """TRIANG: materia_id null → 201."""
        response = await client_coordinador.post(
            "/api/tareas",
            json={"asignado_a": str(_mock_user.id), "descripcion": "Inst task"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["materia_id"] is None

    async def test_06_get_tarea_ok(self, client_coordinador, _mock_user):
        """TRIANG: GET /api/tareas/{id} → 200."""
        create_resp = await client_coordinador.post(
            "/api/tareas",
            json={"asignado_a": str(_mock_user.id), "descripcion": "Get test"},
        )
        tarea_id = create_resp.json()["id"]

        response = await client_coordinador.get(f"/api/tareas/{tarea_id}")
        assert response.status_code == 200
        assert response.json()["id"] == tarea_id

    async def test_07_get_tarea_404(self, client_coordinador):
        """TRIANG: GET tarea inexistente → 404."""
        response = await client_coordinador.get(f"/api/tareas/{uuid.uuid4()}")
        assert response.status_code == 404

    async def test_08_soft_delete_tarea(self, client_coordinador, _mock_user):
        """TRIANG: DELETE → 204, luego GET → 404."""
        create_resp = await client_coordinador.post(
            "/api/tareas",
            json={"asignado_a": str(_mock_user.id), "descripcion": "To delete"},
        )
        tarea_id = create_resp.json()["id"]

        delete_resp = await client_coordinador.delete(f"/api/tareas/{tarea_id}")
        assert delete_resp.status_code == 204

        get_resp = await client_coordinador.get(f"/api/tareas/{tarea_id}")
        assert get_resp.status_code == 404

    async def test_09_list_aislamiento_tenant(self, client_coordinador, _mock_user):
        """TRIANG: tareas de otro tenant no aparecen en el listado."""
        # Crear tarea en tenant A
        await client_coordinador.post(
            "/api/tareas",
            json={"asignado_a": str(_mock_user.id), "descripcion": "Tenant A task"},
        )

        # Cambiar tenant para simular otro tenant
        otro_user = _mock_user
        otro_user.tenant_id = uuid.uuid4()

        response = await client_coordinador.get("/api/tareas")
        assert response.status_code == 200
        # El listado solo contiene tareas del nuevo tenant (vacío)
        assert len(response.json()) == 0

    async def test_10_profesor_ve_tarea_propia(self, client_profesor, _mock_user):
        """TRIANG: PROFESOR ve tarea donde es asignado_a."""
        create_resp = await client_profesor.post(
            "/api/tareas",
            json={"asignado_a": str(_mock_user.id), "descripcion": "Propia"},
        )
        tarea_id = create_resp.json()["id"]

        response = await client_profesor.get(f"/api/tareas/{tarea_id}")
        assert response.status_code == 200

    async def test_11_profesor_no_ve_tarea_ajena(self, client_profesor, _mock_user):
        """TRIANG: PROFESOR no ve tarea donde NO es asignado_a/asignado_por."""
        # Crear tarea con el mock user (asignado_a = asignado_por)
        create_resp = await client_profesor.post(
            "/api/tareas",
            json={"asignado_a": str(_mock_user.id), "descripcion": "Ajena"},
        )
        tarea_id = create_resp.json()["id"]

        # Cambiar el mock user para que sea diferente del asignado_a/asignado_por
        _mock_user.id = uuid.uuid4()

        response = await client_profesor.get(f"/api/tareas/{tarea_id}")
        assert response.status_code == 404

    async def test_12_tarea_sin_permiso_403(self, client_sin_permiso):
        """TRIANG: usuario sin permiso recibe 403."""
        response = await client_sin_permiso.post(
            "/api/tareas",
            json={"asignado_a": str(uuid.uuid4()), "descripcion": "No perm"},
        )
        assert response.status_code == 403

    async def test_13_extra_field_422(self, client_coordinador):
        """TRIANG: campo extra en body → 422."""
        response = await client_coordinador.post(
            "/api/tareas",
            json={
                "asignado_a": str(uuid.uuid4()),
                "descripcion": "X",
                "extra": "no",
            },
        )
        assert response.status_code == 422

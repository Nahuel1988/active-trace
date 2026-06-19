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
def app():
    return create_app()


@pytest.fixture
def _mock_user():
    from unittest.mock import MagicMock

    user = MagicMock()
    user.id = uuid.uuid4()
    user.actor_id = user.id
    user.tenant_id = uuid.uuid4()
    user.impersonated = False
    return user


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

    async def test_01_delegar_ok(self, client_coordinador, _mock_user):
        """RED: POST /api/tareas/{id}/asignar → 200, asignado_a actualizado."""
        nuevo_asignado = uuid.uuid4()

        resp = await client_coordinador.post(
            "/api/tareas",
            json={"asignado_a": str(_mock_user.id), "descripcion": "Deleg test"},
        )
        tarea_id = resp.json()["id"]

        delegar_resp = await client_coordinador.post(
            f"/api/tareas/{tarea_id}/asignar",
            json={"asignado_a": str(nuevo_asignado)},
        )
        assert delegar_resp.status_code == 200
        data = delegar_resp.json()
        assert data["asignado_a"] == str(nuevo_asignado)

    async def test_02_delegar_conserva_trazabilidad(self, client_coordinador, _mock_user):
        """TRIANG: asignado_por = quien delegó (el de la sesión)."""
        original_asignado = _mock_user.id
        nuevo_asignado = uuid.uuid4()

        resp = await client_coordinador.post(
            "/api/tareas",
            json={"asignado_a": str(original_asignado), "descripcion": "Trace test"},
        )
        tarea_id = resp.json()["id"]
        creador_id = resp.json()["asignado_por"]

        # Delegar
        delegar_resp = await client_coordinador.post(
            f"/api/tareas/{tarea_id}/asignar",
            json={"asignado_a": str(nuevo_asignado)},
        )
        data = delegar_resp.json()
        assert data["asignado_a"] == str(nuevo_asignado)
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

    async def test_04_profesor_delega_propia_ok(self, client_profesor, _mock_user):
        """TRIANG: PROFESOR delega tarea donde es asignado_a → 200."""
        nuevo_asignado = uuid.uuid4()

        resp = await client_profesor.post(
            "/api/tareas",
            json={"asignado_a": str(_mock_user.id), "descripcion": "Prof own"},
        )
        tarea_id = resp.json()["id"]

        delegar_resp = await client_profesor.post(
            f"/api/tareas/{tarea_id}/asignar",
            json={"asignado_a": str(nuevo_asignado)},
        )
        assert delegar_resp.status_code == 200

    async def test_05_profesor_delega_ajena_404(self, client_profesor, _mock_user):
        """TRIANG: PROFESOR delega tarea ajena → 404."""
        otro_id = uuid.uuid4()
        resp = await client_profesor.post(
            "/api/tareas",
            json={"asignado_a": str(otro_id), "descripcion": "Not yours"},
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

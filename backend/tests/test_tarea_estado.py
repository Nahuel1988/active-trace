"""Tests de la máquina de estados de tareas (C-16, spec: tarea-lifecycle).

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


def _crear_tarea_para_estado(coord_client, user_id) -> str:
    """Helper: crea tarea Pendiente y retorna su ID."""
    import httpx
    resp = coord_client.post(
        "/api/tareas",
        json={"asignado_a": str(user_id), "descripcion": "State test"},
    )
    if isinstance(resp, httpx.Response):
        return resp.json()["id"]
    return None


# ---------------------------------------------------------------------------
# Tests — Máquina de estados
# ---------------------------------------------------------------------------


class TestTareaEstado:
    """Scenario: transiciones de estado (máquina D-02)."""

    async def test_01_pendiente_a_enprogreso_ok(self, client_coordinador, _mock_user):
        """RED: Pendiente → EnProgreso → 200."""
        resp = await client_coordinador.post(
            "/api/tareas",
            json={"asignado_a": str(_mock_user.id), "descripcion": "Estado test"},
        )
        tarea_id = resp.json()["id"]

        patch_resp = await client_coordinador.patch(
            f"/api/tareas/{tarea_id}/estado",
            json={"estado": "EnProgreso"},
        )
        assert patch_resp.status_code == 200
        assert patch_resp.json()["estado"] == "EnProgreso"

    async def test_02_enprogreso_a_resuelta_ok(self, client_coordinador, _mock_user):
        """TRIANG: EnProgreso → Resuelta → 200."""
        resp = await client_coordinador.post(
            "/api/tareas",
            json={"asignado_a": str(_mock_user.id), "descripcion": "Resolve test"},
        )
        tarea_id = resp.json()["id"]

        # Pendiente → EnProgreso
        await client_coordinador.patch(
            f"/api/tareas/{tarea_id}/estado",
            json={"estado": "EnProgreso"},
        )

        # EnProgreso → Resuelta
        patch_resp = await client_coordinador.patch(
            f"/api/tareas/{tarea_id}/estado",
            json={"estado": "Resuelta"},
        )
        assert patch_resp.status_code == 200
        assert patch_resp.json()["estado"] == "Resuelta"

    async def test_03_transicion_invalida_400(self, client_coordinador, _mock_user):
        """TRIANG: Pendiente → Resuelta → 400 (salta EnProgreso)."""
        resp = await client_coordinador.post(
            "/api/tareas",
            json={"asignado_a": str(_mock_user.id), "descripcion": "Invalid"},
        )
        tarea_id = resp.json()["id"]

        patch_resp = await client_coordinador.patch(
            f"/api/tareas/{tarea_id}/estado",
            json={"estado": "Resuelta"},
        )
        assert patch_resp.status_code == 400

    async def test_04_cancelada_es_terminal_400(self, client_coordinador, _mock_user):
        """TRIANG: Cancelada es terminal → cualquier transición → 400."""
        resp = await client_coordinador.post(
            "/api/tareas",
            json={"asignado_a": str(_mock_user.id), "descripcion": "Cancel test"},
        )
        tarea_id = resp.json()["id"]

        # Pendiente → Cancelada
        await client_coordinador.patch(
            f"/api/tareas/{tarea_id}/estado",
            json={"estado": "Cancelada"},
        )

        # Cancelada → EnProgreso → 400
        patch_resp = await client_coordinador.patch(
            f"/api/tareas/{tarea_id}/estado",
            json={"estado": "EnProgreso"},
        )
        assert patch_resp.status_code == 400

    async def test_05_enprogreso_a_pendiente_ok(self, client_coordinador, _mock_user):
        """TRIANG: EnProgreso → Pendiente (devolver) → 200."""
        resp = await client_coordinador.post(
            "/api/tareas",
            json={"asignado_a": str(_mock_user.id), "descripcion": "Devolver"},
        )
        tarea_id = resp.json()["id"]

        await client_coordinador.patch(
            f"/api/tareas/{tarea_id}/estado",
            json={"estado": "EnProgreso"},
        )

        patch_resp = await client_coordinador.patch(
            f"/api/tareas/{tarea_id}/estado",
            json={"estado": "Pendiente"},
        )
        assert patch_resp.status_code == 200
        assert patch_resp.json()["estado"] == "Pendiente"

    async def test_06_reapertura_coordinador_ok(self, client_coordinador, _mock_user):
        """TRIANG: Resuelta → EnProgreso por COORD → 200."""
        resp = await client_coordinador.post(
            "/api/tareas",
            json={"asignado_a": str(_mock_user.id), "descripcion": "Reopen"},
        )
        tarea_id = resp.json()["id"]

        await client_coordinador.patch(
            f"/api/tareas/{tarea_id}/estado",
            json={"estado": "EnProgreso"},
        )
        await client_coordinador.patch(
            f"/api/tareas/{tarea_id}/estado",
            json={"estado": "Resuelta"},
        )

        # Reapertura
        patch_resp = await client_coordinador.patch(
            f"/api/tareas/{tarea_id}/estado",
            json={"estado": "EnProgreso"},
        )
        assert patch_resp.status_code == 200
        assert patch_resp.json()["estado"] == "EnProgreso"

    async def test_07_reapertura_profesor_403(self, client_profesor, _mock_user):
        """TRIANG: Resuelta → EnProgreso por PROFESOR → 403."""
        # Primero crear la tarea como coordinador para tenerla
        coord = client_profesor  # reuse fixture, pero el scope es "propio"

        resp = await client_profesor.post(
            "/api/tareas",
            json={"asignado_a": str(_mock_user.id), "descripcion": "Reopen prof"},
        )
        tarea_id = resp.json()["id"]

        await client_profesor.patch(
            f"/api/tareas/{tarea_id}/estado",
            json={"estado": "EnProgreso"},
        )
        await client_profesor.patch(
            f"/api/tareas/{tarea_id}/estado",
            json={"estado": "Resuelta"},
        )

        # PROFESOR intenta reabrir → 403
        patch_resp = await client_profesor.patch(
            f"/api/tareas/{tarea_id}/estado",
            json={"estado": "EnProgreso"},
        )
        assert patch_resp.status_code == 403

    async def test_08_estado_invalido_422(self, client_coordinador):
        """TRIANG: estado inexistente → 422."""
        tarea_id = uuid.uuid4()
        response = await client_coordinador.patch(
            f"/api/tareas/{tarea_id}/estado",
            json={"estado": "EstadoInvalido"},
        )
        assert response.status_code == 422

    async def test_09_cambiar_estado_tarea_ajena_404(self, client_profesor, _mock_user):
        """TRIANG: PROFESOR cambia estado de tarea ajena → 404."""
        otro_id = uuid.uuid4()
        resp = await client_profesor.post(
            "/api/tareas",
            json={"asignado_a": str(otro_id), "descripcion": "Ajena"},
        )
        tarea_id = resp.json()["id"]

        # Cambiar mock para que sea otro usuario
        _mock_user.id = uuid.uuid4()

        patch_resp = await client_profesor.patch(
            f"/api/tareas/{tarea_id}/estado",
            json={"estado": "EnProgreso"},
        )
        assert patch_resp.status_code == 404

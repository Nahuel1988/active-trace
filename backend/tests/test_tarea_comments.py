"""Tests de comentarios en tareas (C-16, spec: tarea-comments).

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
# Helpers
# ---------------------------------------------------------------------------


async def _crear_tarea(cliente, user_id) -> str:
    """Crea una tarea y retorna su ID."""
    resp = await cliente.post(
        "/api/tareas",
        json={"asignado_a": str(user_id), "descripcion": "Comentarios test"},
    )
    return resp.json()["id"]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestTareaComentarios:
    """Scenario: comentarios en hilo append-only por tarea."""

    async def test_01_crear_comentario_ok(self, client_coordinador, _mock_user):
        """RED: POST /api/tareas/{id}/comentarios → 201, autor_id = sesión."""
        tarea_id = await _crear_tarea(client_coordinador, _mock_user.id)

        resp = await client_coordinador.post(
            f"/api/tareas/{tarea_id}/comentarios",
            json={"texto": "Mi comentario"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["texto"] == "Mi comentario"
        assert data["autor_id"] == str(_mock_user.id)
        assert data["tarea_id"] == tarea_id

    async def test_02_comentario_autor_body_rechazado(self, client_coordinador, _mock_user):
        """TRIANG: autor_id en body → 422 (extra='forbid')."""
        tarea_id = await _crear_tarea(client_coordinador, _mock_user.id)

        resp = await client_coordinador.post(
            f"/api/tareas/{tarea_id}/comentarios",
            json={"texto": "Texto", "autor_id": str(uuid.uuid4())},
        )
        assert resp.status_code == 422

    async def test_03_listar_comentarios_vacio(self, client_coordinador, _mock_user):
        """TRIANG: GET comentarios → lista vacía si no hay."""
        tarea_id = await _crear_tarea(client_coordinador, _mock_user.id)

        resp = await client_coordinador.get(
            f"/api/tareas/{tarea_id}/comentarios",
        )
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_04_listar_comentarios_orden_cronologico(
        self, client_coordinador, _mock_user
    ):
        """TRIANG: múltiples comentarios ordenados por creado_at ASC."""
        tarea_id = await _crear_tarea(client_coordinador, _mock_user.id)

        # Crear 3 comentarios
        await client_coordinador.post(
            f"/api/tareas/{tarea_id}/comentarios",
            json={"texto": "Primero"},
        )
        await client_coordinador.post(
            f"/api/tareas/{tarea_id}/comentarios",
            json={"texto": "Segundo"},
        )
        await client_coordinador.post(
            f"/api/tareas/{tarea_id}/comentarios",
            json={"texto": "Tercero"},
        )

        resp = await client_coordinador.get(
            f"/api/tareas/{tarea_id}/comentarios",
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 3
        assert data[0]["texto"] == "Primero"
        assert data[1]["texto"] == "Segundo"
        assert data[2]["texto"] == "Tercero"

    async def test_05_comentarios_aislamiento_tenant_404(
        self, client_coordinador, _mock_user
    ):
        """TRIANG: comentarios de tarea de otro tenant → 404."""
        tarea_id = uuid.uuid4()
        resp = await client_coordinador.get(
            f"/api/tareas/{tarea_id}/comentarios",
        )
        assert resp.status_code == 404

    async def test_06_comentario_tarea_inexistente_404(
        self, client_coordinador
    ):
        """TRIANG: comentar en tarea que no existe → 404."""
        resp = await client_coordinador.post(
            f"/api/tareas/{uuid.uuid4()}/comentarios",
            json={"texto": "Perdido"},
        )
        assert resp.status_code == 404

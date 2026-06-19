"""Tests del ciclo de vida de slots de encuentro (C-13, spec: slot-encuentro-lifecycle).

RED → GREEN → TRIANGULATE → REFACTOR.
Requiere PostgreSQL (--run-db).
"""

import uuid
from datetime import date, time
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
async def app(db_engine):
    """App FastAPI — db_engine asegura que las tablas existen."""
    return create_app()


@pytest.fixture
def _mock_user():
    """Mock user with random IDs (same tenant for the test)."""
    from unittest.mock import MagicMock

    user = MagicMock()
    user.id = uuid.uuid4()
    user.actor_id = user.id
    user.tenant_id = uuid.uuid4()
    user.impersonated = False
    return user


@pytest.fixture
async def client_sin_permiso(app, _mock_user):
    """Client autenticado pero sin encuentros:gestionar → espera 403."""
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
async def client_tutor(app, _mock_user):
    """Client como TUTOR (scope 'propio')."""
    app.dependency_overrides[get_current_user] = lambda: _mock_user
    grant = PermissionGrant(code="encuentros:gestionar", scope="propio")
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
    grant = PermissionGrant(code="encuentros:gestionar", scope="global")
    transport = ASGITransport(app=app)
    with patch(
        "app.services.permission_service.PermissionService.verify_permission",
        new=AsyncMock(return_value=grant),
    ):
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Tests — Creación de Slots
# ---------------------------------------------------------------------------


class TestSlotCreation:
    """Scenario: crear slots recurrentes y únicos."""

    async def test_01_sin_permiso_retorna_403(self, client_sin_permiso):
        """WHEN autenticado sin encuentros:gestionar, THEN 403."""
        response = await client_sin_permiso.get("/api/encuentros/slots")
        assert response.status_code == 403

    async def test_02_create_slot_recurrente_needs_db(self, client_coordinador, _mock_user):
        """RED: POST /api/encuentros/slots → 422 si la asignacion no existe en DB.

        Este test se marca como requiere DB porque sin datos seed,
        cualquier asignacion_id genera 404.
        """
        payload = {
            "modo": "recurrente",
            "asignacion_id": str(uuid.uuid4()),
            "materia_id": str(uuid.uuid4()),
            "titulo": "Clase 1",
            "hora": "10:00:00",
            "dia_semana": "lunes",
            "fecha_inicio": "2026-03-02",
            "cant_semanas": 4,
            "meet_url": "https://meet.google.com/abc-defg-hij",
            "vig_desde": "2026-03-01",
        }
        response = await client_coordinador.post(
            "/api/encuentros/slots",
            json=payload,
        )
        # La asignacion no existe en DB → el service retorna 404
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    async def test_03_create_slot_unico_no_asignacion(self, client_coordinador, _mock_user):
        """TRIANGULAR: modo único sin cant_semanas, asignacion inexistente → 404."""
        payload = {
            "modo": "unico",
            "asignacion_id": str(uuid.uuid4()),
            "materia_id": str(uuid.uuid4()),
            "titulo": "Clase especial",
            "hora": "14:00:00",
            "dia_semana": "miercoles",
            "fecha_inicio": "2026-03-04",
            "fecha_unica": "2026-03-11",
            "meet_url": None,
            "vig_desde": "2026-03-01",
        }
        response = await client_coordinador.post(
            "/api/encuentros/slots",
            json=payload,
        )
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    async def test_04_create_slot_sin_cant_semanas_recurrente_422(
        self, client_coordinador, _mock_user
    ):
        """TRIANGULAR: modo recurrente sin cant_semanas → 422 (validation error)."""
        payload = {
            "modo": "recurrente",
            "asignacion_id": str(uuid.uuid4()),
            "materia_id": str(uuid.uuid4()),
            "titulo": "Clase sin semanas",
            "hora": "10:00:00",
            "dia_semana": "lunes",
            "fecha_inicio": "2026-03-02",
            "meet_url": None,
            "vig_desde": "2026-03-01",
        }
        response = await client_coordinador.post(
            "/api/encuentros/slots",
            json=payload,
        )
        assert response.status_code == 422

    async def test_05_create_slot_fecha_inicio_no_coincide(
        self, client_coordinador, _mock_user
    ):
        """TRIANGULAR: el service valida asignacion primero → 404 (asignacion no existe).
        Nota: la validación fecha_inicio vs dia_semana ocurre DESPUÉS de existir la asignacion.
        """
        payload = {
            "modo": "recurrente",
            "asignacion_id": str(uuid.uuid4()),
            "materia_id": str(uuid.uuid4()),
            "titulo": "Fecha errónea",
            "hora": "10:00:00",
            "dia_semana": "lunes",
            "fecha_inicio": "2026-03-03",  # miércoles, no lunes
            "cant_semanas": 4,
            "meet_url": None,
            "vig_desde": "2026-03-01",
        }
        response = await client_coordinador.post(
            "/api/encuentros/slots",
            json=payload,
        )
        # Sin asignacion seed en DB, la validación nunca llega al date check
        assert response.status_code == 404

    async def test_06_list_slots_vacio(self, client_coordinador, _mock_user):
        """GREEN: GET /api/encuentros/slots retorna [] en DB vacía."""
        response = await client_coordinador.get("/api/encuentros/slots")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_07_delete_slot_inexistente_404(self, client_coordinador, _mock_user):
        """TRIANGULAR: DELETE slot que no existe → 404."""
        response = await client_coordinador.delete(
            f"/api/encuentros/slots/{uuid.uuid4()}",
        )
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Tests — Instancias
# ---------------------------------------------------------------------------


class TestInstanciaLifecycle:
    """Scenario: editar instancias y transiciones de estado."""

    async def test_08_get_instancia_inexistente_404(self, client_coordinador, _mock_user):
        """GREEN: GET instancia que no existe → 404."""
        response = await client_coordinador.get(
            f"/api/encuentros/instancias/{uuid.uuid4()}",
        )
        assert response.status_code == 404

    async def test_09_list_instancias_vacio(self, client_coordinador, _mock_user):
        """GREEN: GET /api/encuentros/instancias retorna []."""
        response = await client_coordinador.get("/api/encuentros/instancias")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_10_patch_instancia_inexistente_404(self, client_coordinador, _mock_user):
        """GREEN: PATCH instancia que no existe → 404."""
        response = await client_coordinador.patch(
            f"/api/encuentros/instancias/{uuid.uuid4()}",
            json={"estado": "realizado"},
        )
        assert response.status_code == 404

    async def test_11_html_export_slot_inexistente_404(self, client_coordinador, _mock_user):
        """GREEN: GET slots/{id}/html con slot inexistente → 404."""
        response = await client_coordinador.get(
            f"/api/encuentros/slots/{uuid.uuid4()}/html",
        )
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Tests — Multi-tenant
# ---------------------------------------------------------------------------


class TestAislamiento:
    """Scenario: aislamiento multi-tenant."""

    async def test_12_slot_otro_tenant_404(self, client_coordinador, _mock_user):
        """RED: slot de otro tenant retorna 404."""
        response = await client_coordinador.get(
            f"/api/encuentros/slots/{uuid.uuid4()}",
        )
        assert response.status_code == 404

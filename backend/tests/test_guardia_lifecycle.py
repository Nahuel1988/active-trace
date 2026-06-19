"""Tests del ciclo de vida de guardias (C-13, spec: guardia-lifecycle).

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
    """Client autenticado pero sin guardias:registrar → espera 403."""
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
    grant = PermissionGrant(code="guardias:registrar", scope="propio")
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
    grant = PermissionGrant(code="guardias:registrar", scope="global")
    transport = ASGITransport(app=app)
    with patch(
        "app.services.permission_service.PermissionService.verify_permission",
        new=AsyncMock(return_value=grant),
    ):
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Tests — Creación de Guardias
# ---------------------------------------------------------------------------


class TestGuardiaCreation:
    """Scenario: registrar guardias."""

    async def test_01_sin_permiso_retorna_403(self, client_sin_permiso):
        """WHEN autenticado sin guardias:registrar, THEN 403."""
        response = await client_sin_permiso.get("/api/guardias")
        assert response.status_code == 403

    async def test_02_create_guardia_asignacion_inexistente_404(
        self, client_coordinador, _mock_user
    ):
        """RED: POST /api/guardias con asignacion_id aleatorio → 404."""
        payload = {
            "asignacion_id": str(uuid.uuid4()),
            "materia_id": str(uuid.uuid4()),
            "carrera_id": str(uuid.uuid4()),
            "cohorte_id": str(uuid.uuid4()),
            "dia": "lunes",
            "horario": "14:00–15:00",
            "comentarios": None,
        }
        response = await client_coordinador.post("/api/guardias", json=payload)
        assert response.status_code == 404

    async def test_03_list_guardias_vacio(self, client_coordinador, _mock_user):
        """GREEN: GET /api/guardias retorna [] en DB vacía."""
        response = await client_coordinador.get("/api/guardias")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_04_get_guardia_inexistente_404(self, client_coordinador, _mock_user):
        """GREEN: GET /api/guardias/{id} con ID aleatorio → 404."""
        response = await client_coordinador.get(f"/api/guardias/{uuid.uuid4()}")
        assert response.status_code == 404

    async def test_05_patch_estado_guardia_inexistente_404(
        self, client_coordinador, _mock_user
    ):
        """GREEN: PATCH estado de guardia inexistente → 404."""
        response = await client_coordinador.patch(
            f"/api/guardias/{uuid.uuid4()}/estado",
            json={"estado": "realizada"},
        )
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Tests — Export CSV
# ---------------------------------------------------------------------------


class TestExportCSV:
    """Scenario: exportar guardias como CSV."""

    async def test_06_export_csv_vacio(self, client_coordinador, _mock_user):
        """GREEN: GET /api/guardias/export retorna CSV con headers."""
        response = await client_coordinador.get("/api/guardias/export/csv")
        assert response.status_code == 200
        assert "text/csv" in response.headers.get("content-type", "").lower()
        content = response.text
        assert "fecha_creacion" in content
        assert "tutor" in content
        assert "materia" in content


# ---------------------------------------------------------------------------
# Tests — Multi-tenant / Permisos
# ---------------------------------------------------------------------------


class TestAislamiento:
    """Scenario: aislamiento multi-tenant y permisos."""

    async def test_07_tutor_create_otro_tenant_404(self, client_tutor, _mock_user):
        """RED: TUTOR crea guardia con asignacion_id aleatorio → 404."""
        payload = {
            "asignacion_id": str(uuid.uuid4()),
            "materia_id": str(uuid.uuid4()),
            "carrera_id": str(uuid.uuid4()),
            "cohorte_id": str(uuid.uuid4()),
            "dia": "lunes",
            "horario": "14:00–15:00",
            "comentarios": None,
        }
        response = await client_tutor.post("/api/guardias", json=payload)
        assert response.status_code == 404

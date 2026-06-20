"""Router endpoint tests for análisis and monitores (C-11).

Sigue el patrón de test_calificaciones_endpoints.py:
- client sin auth → 401
- client_no_perm → 403
- client_analisis (permiso atrasados:ver) → 200
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.dependencies import get_current_user
from app.core.permissions import PermissionGrant
from app.main import create_app
from app.schemas.analisis import AtrasadosResponse, EntregasPendientesResponse, MonitorResponse, NotasFinalesResponse, RankingResponse, ReporteRapidoResponse

pytestmark = pytest.mark.requires_db


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
def _mock_user():
    user = __import__("unittest").mock.MagicMock()
    user.id = uuid.uuid4()
    user.tenant_id = uuid.uuid4()
    user.actor_id = uuid.uuid4()
    return user


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def _make_client_with_perm(app, perm_code, scope="global"):
    """Create a context manager that yields an HTTP client with the given permission."""

    async def _get_user():
        user = __import__("unittest").mock.MagicMock()
        user.id = uuid.uuid4()
        user.tenant_id = uuid.uuid4()
        user.actor_id = uuid.uuid4()
        return user

    app.dependency_overrides[get_current_user] = _get_user
    grant = PermissionGrant(code=perm_code, scope=scope)
    transport = ASGITransport(app=app)
    with patch(
        "app.services.permission_service.PermissionService.verify_permission",
        new=AsyncMock(return_value=grant),
    ):
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
    app.dependency_overrides.clear()


@pytest.fixture
async def client_no_perm(app, _mock_user):
    async def _get_user():
        return _mock_user

    app.dependency_overrides[get_current_user] = _get_user
    transport = ASGITransport(app=app)
    with patch(
        "app.services.permission_service.PermissionService.verify_permission",
        new=AsyncMock(return_value=None),
    ):
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
    app.dependency_overrides.clear()


@pytest.fixture
async def client_analisis(app, _mock_user):
    async def _get_user():
        return _mock_user

    app.dependency_overrides[get_current_user] = _get_user
    grant = PermissionGrant(code="atrasados:ver", scope="global")
    transport = ASGITransport(app=app)
    with (
        patch(
            "app.services.permission_service.PermissionService.verify_permission",
            new=AsyncMock(return_value=grant),
        ),
        patch(
            "app.api.v1.routers.analisis.audit_action",
            new=AsyncMock(return_value=MagicMock()),
        ),
        patch(
            "app.api.v1.routers.monitores.audit_action",
            new=AsyncMock(return_value=MagicMock()),
        ),
    ):
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
    app.dependency_overrides.clear()


# ============================================================================
# 8.1 — Atrasados endpoint
# ============================================================================


class TestGetAtrasadosEndpoint:
    """GET /api/v1/analisis/atrasados — tasks 8.1, 8.8, 8.9."""

    async def test_sin_auth_401(self, client):
        resp = await client.get("/api/v1/analisis/atrasados?materia_id=" + str(uuid.uuid4()))
        assert resp.status_code == 401

    async def test_sin_permiso_403(self, client_no_perm):
        resp = await client_no_perm.get(
            "/api/v1/analisis/atrasados?materia_id=" + str(uuid.uuid4()),
        )
        assert resp.status_code == 403

    async def test_con_permiso_200(self, client_analisis):
        with patch(
            "app.services.analisis_service.AnalisisService.get_atrasados",
            new=AsyncMock(return_value=AtrasadosResponse(items=[], total=0)),
        ):
            resp = await client_analisis.get(
                "/api/v1/analisis/atrasados?materia_id=" + str(uuid.uuid4()),
            )
        assert resp.status_code == 200

    async def test_materia_id_invalido_422(self, client_analisis):
        resp = await client_analisis.get("/api/v1/analisis/atrasados?materia_id=invalido")
        assert resp.status_code == 422


# ============================================================================
# 8.2 — Ranking endpoint
# ============================================================================


class TestGetRankingEndpoint:
    """GET /api/v1/analisis/ranking — tasks 8.2, 8.8."""

    async def test_sin_permiso_403(self, client_no_perm):
        resp = await client_no_perm.get(
            "/api/v1/analisis/ranking?materia_id=" + str(uuid.uuid4()),
        )
        assert resp.status_code == 403

    async def test_con_permiso_200(self, client_analisis):
        with patch(
            "app.services.analisis_service.AnalisisService.get_ranking",
            new=AsyncMock(return_value=RankingResponse(items=[])),
        ):
            resp = await client_analisis.get(
                "/api/v1/analisis/ranking?materia_id=" + str(uuid.uuid4()),
            )
        assert resp.status_code == 200


# ============================================================================
# 8.3 — Reportes endpoint
# ============================================================================


class TestGetReporteRapidoEndpoint:
    """GET /api/v1/analisis/reportes — tasks 8.3, 8.8."""

    async def test_sin_permiso_403(self, client_no_perm):
        resp = await client_no_perm.get(
            "/api/v1/analisis/reportes?materia_id=" + str(uuid.uuid4()),
        )
        assert resp.status_code == 403

    async def test_con_permiso_200(self, client_analisis):
        with patch(
            "app.services.analisis_service.AnalisisService.get_reporte_rapido",
            new=AsyncMock(return_value=ReporteRapidoResponse(
                total_alumnos=0, total_actividades=0, tasa_aprobacion_pct=0.0,
                alumnos_atrasados=0, alumnos_al_dia=0, sin_datos=True,
            )),
        ):
            resp = await client_analisis.get(
                "/api/v1/analisis/reportes?materia_id=" + str(uuid.uuid4()),
            )
        assert resp.status_code == 200


# ============================================================================
# 8.4 — Notas finales endpoint
# ============================================================================


class TestGetNotasFinalesEndpoint:
    """GET /api/v1/analisis/notas-finales — tasks 8.4, 8.8."""

    async def test_sin_permiso_403(self, client_no_perm):
        resp = await client_no_perm.get(
            "/api/v1/analisis/notas-finales?materia_id=" + str(uuid.uuid4()),
        )
        assert resp.status_code == 403

    async def test_con_permiso_200(self, client_analisis):
        with patch(
            "app.services.analisis_service.AnalisisService.get_notas_finales",
            new=AsyncMock(return_value=NotasFinalesResponse(items=[])),
        ):
            resp = await client_analisis.get(
                "/api/v1/analisis/notas-finales?materia_id=" + str(uuid.uuid4()),
            )
        assert resp.status_code == 200


# ============================================================================
# 8.5 — Entregas pendientes endpoint
# ============================================================================


class TestGetEntregasPendientesEndpoint:
    """GET /api/v1/analisis/entregas-pendientes — tasks 8.5, 8.8."""

    async def test_sin_permiso_403(self, client_no_perm):
        resp = await client_no_perm.get(
            "/api/v1/analisis/entregas-pendientes?materia_id=" + str(uuid.uuid4()),
        )
        assert resp.status_code == 403

    async def test_con_permiso_200(self, client_analisis):
        with patch(
            "app.services.analisis_service.AnalisisService.get_entregas_pendientes",
            new=AsyncMock(return_value=EntregasPendientesResponse(items=[], todas_corregidas=True)),
        ):
            resp = await client_analisis.get(
                "/api/v1/analisis/entregas-pendientes?materia_id=" + str(uuid.uuid4()),
            )
        assert resp.status_code == 200


# ============================================================================
# 8.6 — Monitor general endpoint
# ============================================================================


class TestGetMonitorGeneralEndpoint:
    """GET /api/v1/monitores/general — tasks 8.6, 8.8."""

    async def test_sin_permiso_403(self, client_no_perm):
        resp = await client_no_perm.get("/api/v1/monitores/general")
        assert resp.status_code == 403

    async def test_con_permiso_200(self, client_analisis):
        with patch(
            "app.services.monitor_service.MonitorService.get_monitor_general",
            new=AsyncMock(return_value=MonitorResponse(items=[], total=0, limit=50, offset=0)),
        ):
            resp = await client_analisis.get("/api/v1/monitores/general")
        assert resp.status_code == 200


# ============================================================================
# 8.7 — Monitor seguimiento endpoint
# ============================================================================


class TestGetMonitorSeguimientoEndpoint:
    """GET /api/v1/monitores/seguimiento — tasks 8.7, 8.8."""

    async def test_sin_permiso_403(self, client_no_perm):
        resp = await client_no_perm.get("/api/v1/monitores/seguimiento")
        assert resp.status_code == 403

    async def test_con_permiso_200(self, client_analisis):
        with patch(
            "app.services.monitor_service.MonitorService.get_monitor_seguimiento",
            new=AsyncMock(return_value=MonitorResponse(items=[], total=0, limit=50, offset=0)),
        ):
            resp = await client_analisis.get("/api/v1/monitores/seguimiento")
        assert resp.status_code == 200

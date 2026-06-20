"""Router endpoint tests para calificaciones (Grupo 13).

Sigue el patrón de test_padron_endpoints.py:
- client sin auth → 401
- client_no_perm (permiso denegado) → 403
- client_importar / client_configurar / client_vaciar con permiso → status esperado
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.dependencies import get_current_user
from app.core.permissions import PermissionGrant
from app.main import create_app

pytestmark = pytest.mark.requires_db


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
def _mock_user():
    user = MagicMock()
    user.id = uuid.uuid4()
    user.tenant_id = uuid.uuid4()
    user.actor_id = uuid.uuid4()
    return user


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


def _make_client_fixture(perm_code: str, scope: str = "global"):
    """Factory para crear fixtures de client con permisos específicos."""

    async def _fixture(app, _mock_user):
        async def _get_user():
            return _mock_user

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

    return _fixture


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
async def client_importar(app, _mock_user):
    async def _get_user():
        return _mock_user

    app.dependency_overrides[get_current_user] = _get_user
    grant = PermissionGrant(code="calificaciones:importar", scope="global")
    transport = ASGITransport(app=app)
    with patch(
        "app.services.permission_service.PermissionService.verify_permission",
        new=AsyncMock(return_value=grant),
    ):
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
    app.dependency_overrides.clear()


@pytest.fixture
async def client_configurar(app, _mock_user):
    async def _get_user():
        return _mock_user

    app.dependency_overrides[get_current_user] = _get_user
    grant = PermissionGrant(code="calificaciones:configurar-umbral", scope="global")
    transport = ASGITransport(app=app)
    with patch(
        "app.services.permission_service.PermissionService.verify_permission",
        new=AsyncMock(return_value=grant),
    ):
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
    app.dependency_overrides.clear()


@pytest.fixture
async def client_vaciar(app, _mock_user):
    async def _get_user():
        return _mock_user

    app.dependency_overrides[get_current_user] = _get_user
    grant = PermissionGrant(code="calificaciones:vaciar", scope="global")
    transport = ASGITransport(app=app)
    with patch(
        "app.services.permission_service.PermissionService.verify_permission",
        new=AsyncMock(return_value=grant),
    ):
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
    app.dependency_overrides.clear()


# ============================================================================
# Tests
# ============================================================================


class TestPreviewEndpoint:
    """POST /api/v1/calificaciones/preview — task 13.1-13.2."""

    async def test_preview_sin_token_retorna_401(self, client):
        response = await client.post("/api/v1/calificaciones/preview")
        assert response.status_code == 401

    async def test_preview_sin_permiso_retorna_403(self, client_no_perm):
        response = await client_no_perm.post("/api/v1/calificaciones/preview")
        assert response.status_code == 403

    async def test_preview_con_permiso_retorna_200(self, client_importar):
        response = await client_importar.post(
            "/api/v1/calificaciones/preview",
            files={
                "file": (
                    "notas.csv",
                    b"nombre,apellidos,Parcial (Real),Estado\nJuan,Perez,85,Aprobado",
                    "text/csv",
                )
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "columnas_detectadas" in data
        assert "total_filas" in data
        assert data["total_filas"] == 1


class TestConfirmarEndpoint:
    """POST /api/v1/calificaciones/confirmar — task 13.3-13.4."""

    async def test_confirmar_sin_token_retorna_401(self, client):
        response = await client.post("/api/v1/calificaciones/confirmar", json={})
        assert response.status_code == 401

    async def test_confirmar_sin_permiso_retorna_403(self, client_no_perm):
        response = await client_no_perm.post(
            "/api/v1/calificaciones/confirmar",
            json={
                "materia_id": str(uuid.uuid4()),
                "actividades_seleccionadas": ["Parcial (Real)"],
                "archivo_parseado": [],
                "columnas_detectadas": [],
            },
        )
        assert response.status_code == 403

    async def test_confirmar_con_permiso_retorna_201(self, client_importar):
        """MOCK: el service retorna 3 calificaciones creadas."""
        with patch(
            "app.services.calificacion_service.CalificacionService.confirmar_importacion",
            new=AsyncMock(return_value=3),
        ):
            response = await client_importar.post(
                "/api/v1/calificaciones/confirmar",
                json={
                    "materia_id": str(uuid.uuid4()),
                    "actividades_seleccionadas": ["Parcial (Real)"],
                },
            )
        assert response.status_code == 201
        data = response.json()
        assert data["total_creadas"] == 3


class TestReporteFinalizacionEndpoint:
    """POST /api/v1/calificaciones/reporte-finalizacion — task 13.5-13.6."""

    async def test_reporte_sin_token_retorna_401(self, client):
        response = await client.post("/api/v1/calificaciones/reporte-finalizacion")
        assert response.status_code == 401

    async def test_reporte_sin_permiso_retorna_403(self, client_no_perm):
        response = await client_no_perm.post("/api/v1/calificaciones/reporte-finalizacion")
        assert response.status_code == 403

    async def test_reporte_con_permiso_materia_invalida_422(self, client_importar):
        """materia_id no UUID → 422."""
        response = await client_importar.post(
            "/api/v1/calificaciones/reporte-finalizacion?materia_id=invalido",
            files={
                "file": (
                    "fin.csv",
                    b"nombre,apellidos,Estado\nJuan,Perez,Completo",
                    "text/csv",
                )
            },
        )
        assert response.status_code == 422

    async def test_reporte_con_permiso_retorna_200(self, client_importar):
        """MOCK: service retorna ReporteFinalizacionResponse."""
        from app.schemas.calificacion import ReporteFinalizacionItem, ReporteFinalizacionResponse

        mock_response = ReporteFinalizacionResponse(
            items=[
                ReporteFinalizacionItem(
                    entrada_padron_id=uuid.uuid4(),
                    alumno="Juan Pérez",
                    actividad="Estado",
                    fecha_finalizacion="2025-06-01",
                )
            ]
        )
        with patch(
            "app.services.calificacion_service.CalificacionService.reporte_finalizacion",
            new=AsyncMock(return_value=mock_response),
        ):
            response = await client_importar.post(
                "/api/v1/calificaciones/reporte-finalizacion?materia_id=" + str(uuid.uuid4()),
                files={
                    "file": (
                        "fin.csv",
                        b"nombre,apellidos,Estado\nJuan,Perez,Completo",
                        "text/csv",
                    )
                },
            )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) == 1


class TestListarCalificacionesEndpoint:
    """GET /api/v1/calificaciones — task 13.7-13.8."""

    async def test_listar_sin_token_retorna_401(self, client):
        response = await client.get("/api/v1/calificaciones")
        assert response.status_code == 401

    async def test_listar_sin_permiso_retorna_403(self, client_no_perm):
        response = await client_no_perm.get("/api/v1/calificaciones")
        assert response.status_code == 403

    async def test_listar_materia_invalida_422(self, client_importar):
        response = await client_importar.get(
            "/api/v1/calificaciones?materia_id=invalido"
        )
        assert response.status_code == 422

    async def test_listar_con_permiso_retorna_200(self, client_importar):
        """MOCK: service retorna lista vacía."""
        with patch(
            "app.services.calificacion_service.CalificacionService.get_calificaciones",
            new=AsyncMock(return_value=[]),
        ):
            response = await client_importar.get(
                "/api/v1/calificaciones?materia_id=" + str(uuid.uuid4())
            )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0


class TestGetUmbralEndpoint:
    """GET /api/v1/calificaciones/umbral — task 13.9-13.10."""

    async def test_umbral_sin_token_retorna_401(self, client):
        response = await client.get("/api/v1/calificaciones/umbral")
        assert response.status_code == 401

    async def test_umbral_sin_permiso_retorna_403(self, client_no_perm):
        response = await client_no_perm.get("/api/v1/calificaciones/umbral")
        assert response.status_code == 403

    async def test_umbral_materia_invalida_422(self, client_importar):
        response = await client_importar.get(
            "/api/v1/calificaciones/umbral?materia_id=invalido"
        )
        assert response.status_code == 422


class TestConfigurarUmbralEndpoint:
    """PUT /api/v1/calificaciones/umbral — task 13.11-13.12."""

    async def test_configurar_sin_token_retorna_401(self, client):
        response = await client.put("/api/v1/calificaciones/umbral", json={})
        assert response.status_code == 401

    async def test_configurar_sin_permiso_retorna_403(self, client_no_perm):
        response = await client_no_perm.put(
            "/api/v1/calificaciones/umbral",
            params={"materia_id": str(uuid.uuid4())},
            json={"umbral_pct": 70},
        )
        assert response.status_code == 403

    async def test_configurar_con_permiso_retorna_200(self, client_configurar, app):
        """MOCK: service + db para evitar query real a asignacion."""
        from app.core.dependencies import get_db
        from app.schemas.calificacion import UmbralMateriaResponse

        # Mock db.execute para que la consulta a Asignacion devuelva un ID
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = uuid.uuid4()

        mock_session = MagicMock()
        # execute es async, necesita ser awaitable
        mock_session.execute = AsyncMock(return_value=mock_result)
        # commit y close también son async
        mock_session.commit = AsyncMock()
        mock_session.close = AsyncMock()

        # get_db es un async generator, necesitamos replicarlo
        async def _mock_get_db():
            yield mock_session
            await mock_session.commit()

        app.dependency_overrides[get_db] = _mock_get_db

        mock_umbral = UmbralMateriaResponse(
            id=uuid.uuid4(),
            asignacion_id=uuid.uuid4(),
            materia_id=uuid.uuid4(),
            umbral_pct=70,
            valores_aprobatorios=["Aprobado"],
        )
        with patch(
            "app.services.calificacion_service.UmbralService.configurar_umbral",
            new=AsyncMock(return_value=mock_umbral),
        ):
            response = await client_configurar.put(
                "/api/v1/calificaciones/umbral?materia_id=" + str(uuid.uuid4()),
                json={"umbral_pct": 70, "valores_aprobatorios": ["Aprobado"]},
            )

        app.dependency_overrides.pop(get_db, None)

        assert response.status_code == 200
        data = response.json()
        assert data["umbral_pct"] == 70


class TestVaciarEndpoint:
    """POST /api/v1/calificaciones/vaciar — task 13.13-13.14."""

    async def test_vaciar_sin_token_retorna_401(self, client):
        response = await client.post("/api/v1/calificaciones/vaciar", json={})
        assert response.status_code == 401

    async def test_vaciar_sin_permiso_retorna_403(self, client_no_perm):
        response = await client_no_perm.post(
            "/api/v1/calificaciones/vaciar",
            json={"materia_id": str(uuid.uuid4())},
        )
        assert response.status_code == 403

    async def test_vaciar_con_permiso_retorna_204(self, client_vaciar):
        """MOCK: service retorna 0 afectados."""
        with patch(
            "app.services.calificacion_service.CalificacionService.vaciar_materia",
            new=AsyncMock(return_value=0),
        ):
            response = await client_vaciar.post(
                "/api/v1/calificaciones/vaciar",
                json={"materia_id": str(uuid.uuid4())},
            )
        assert response.status_code == 204


class TestRouterRegistration:
    """Verifica que el router esté registrado y accesible."""

    async def test_calificaciones_paths_existen(self, client):
        """Sin auth, todos los paths retornan 401 (existen)."""
        paths = [
            ("POST", "/api/v1/calificaciones/preview"),
            ("POST", "/api/v1/calificaciones/confirmar"),
            ("POST", "/api/v1/calificaciones/reporte-finalizacion"),
            ("GET", "/api/v1/calificaciones"),
            ("GET", "/api/v1/calificaciones/umbral"),
            ("PUT", "/api/v1/calificaciones/umbral"),
            ("POST", "/api/v1/calificaciones/vaciar"),
        ]
        for method, path in paths:
            response = await client.request(method, path)
            assert response.status_code == 401, f"{method} {path} expected 401, got {response.status_code}"

import uuid
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

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
async def client_cargar(app, _mock_user):
    async def _get_user():
        return _mock_user

    app.dependency_overrides[get_current_user] = _get_user
    grant = PermissionGrant(code="padron:cargar", scope="global")
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
    grant = PermissionGrant(code="padron:vaciar", scope="global")
    transport = ASGITransport(app=app)
    with patch(
        "app.services.permission_service.PermissionService.verify_permission",
        new=AsyncMock(return_value=grant),
    ):
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
    app.dependency_overrides.clear()


@pytest.fixture
async def client_cargar(app, _mock_user):
    async def _get_user():
        return _mock_user

    app.dependency_overrides[get_current_user] = _get_user
    grant = PermissionGrant(code="padron:cargar", scope="global")
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
    grant = PermissionGrant(code="padron:vaciar", scope="global")
    transport = ASGITransport(app=app)
    with patch(
        "app.services.permission_service.PermissionService.verify_permission",
        new=AsyncMock(return_value=grant),
    ):
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
    app.dependency_overrides.clear()


class TestPadronEndpoints:
    async def test_preview_sin_token_retorna_401(self, client) -> None:
        response = await client.post("/api/v1/padron/preview")
        assert response.status_code == 401

    async def test_preview_sin_permiso_retorna_403(self, client_no_perm) -> None:
        response = await client_no_perm.post("/api/v1/padron/preview")
        assert response.status_code == 403

    async def test_preview_con_permiso_retorna_200(self, client_cargar) -> None:
        response = await client_cargar.post(
            "/api/v1/padron/preview",
            files={"file": ("test.csv", b"nombre,apellidos,email,comision\nJuan,Perez,juan@e.com,A", "text/csv")},
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_filas" in data
        assert "columnas_detectadas" in data

    async def test_confirmar_sin_token_retorna_401(self, client) -> None:
        response = await client.post("/api/v1/padron/confirmar", json={})
        assert response.status_code == 401

    async def test_confirmar_sin_permiso_retorna_403(self, client_no_perm) -> None:
        response = await client_no_perm.post(
            "/api/v1/padron/confirmar",
            json={"materia_id": str(uuid.uuid4()), "cohorte_id": str(uuid.uuid4()), "entradas": []},
        )
        assert response.status_code == 403

    async def test_sync_moodle_sin_token_retorna_401(self, client) -> None:
        response = await client.post("/api/v1/padron/sync-moodle", json={})
        assert response.status_code == 401

    async def test_sync_moodle_sin_permiso_retorna_403(self, client_no_perm) -> None:
        response = await client_no_perm.post(
            "/api/v1/padron/sync-moodle",
            json={"materia_id": str(uuid.uuid4()), "cohorte_id": str(uuid.uuid4())},
        )
        assert response.status_code == 403

    async def test_vaciar_sin_token_retorna_401(self, client) -> None:
        response = await client.request("DELETE", "/api/v1/padron/vaciar")
        assert response.status_code == 401

    async def test_vaciar_sin_permiso_retorna_403(self, client_no_perm) -> None:
        import json
        response = await client_no_perm.request(
            "DELETE", "/api/v1/padron/vaciar",
            content=json.dumps({"materia_id": str(uuid.uuid4())}),
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 403

    async def test_versiones_sin_token_retorna_401(self, client) -> None:
        response = await client.get("/api/v1/padron/versiones")
        assert response.status_code == 401

    async def test_versiones_sin_permiso_retorna_403(self, client_no_perm) -> None:
        response = await client_no_perm.get("/api/v1/padron/versiones")
        assert response.status_code == 403

    async def test_versiones_con_permiso_retorna_200(self, client_cargar) -> None:
        from app.schemas.padron import VersionPadronListResponse, VersionPadronResponse
        import datetime

        fake_versiones = VersionPadronListResponse(
            versiones=[VersionPadronResponse(
                id=uuid.uuid4(), materia_id=uuid.uuid4(), cohorte_id=uuid.uuid4(),
                activa=True, total_entradas=5, origen="archivo",
                created_at=datetime.datetime.now(),
            )],
            total=1,
        )
        with patch(
            "app.api.v1.routers.padron.PadronService.list_versiones",
            new=AsyncMock(return_value=fake_versiones.versiones),
        ):
            response = await client_cargar.get("/api/v1/padron/versiones")
        assert response.status_code == 200
        data = response.json()
        assert "versiones" in data
        assert data["total"] == 1

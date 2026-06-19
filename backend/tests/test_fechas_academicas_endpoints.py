"""Integration tests for /api/v1/fechas-academicas endpoints — permission guards."""

import uuid
from unittest.mock import AsyncMock, patch

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
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def _mock_user():
    from unittest.mock import MagicMock
    user = MagicMock()
    user.id = uuid.uuid4()
    user.tenant_id = uuid.uuid4()
    return user


@pytest.fixture
async def client_gestionar(app, _mock_user):
    async def _get_user():
        return _mock_user
    app.dependency_overrides[get_current_user] = _get_user
    grant = PermissionGrant(code="estructura:gestionar", scope="global")
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


class TestFechasAcademicasEndpoints:
    BASE = "/api/v1/fechas-academicas"

    async def test_create_sin_token_retorna_401(self, client: AsyncClient) -> None:
        payload = {
            "materia_id": str(uuid.uuid4()),
            "cohorte_id": str(uuid.uuid4()),
            "tipo": "Parcial",
            "numero": 1,
            "periodo": "2026-1",
            "fecha": "2026-04-15T10:00:00Z",
            "titulo": "Parcial 1",
        }
        response = await client.post(self.BASE, json=payload)
        assert response.status_code == 401

    async def test_create_sin_permiso_retorna_403(self, client_no_perm: AsyncClient) -> None:
        payload = {
            "materia_id": str(uuid.uuid4()),
            "cohorte_id": str(uuid.uuid4()),
            "tipo": "Parcial",
            "numero": 1,
            "periodo": "2026-1",
            "fecha": "2026-04-15T10:00:00Z",
            "titulo": "P1",
        }
        response = await client_no_perm.post(self.BASE, json=payload)
        assert response.status_code == 403

    async def test_tipo_fuera_del_enum_retorna_422(self, client_gestionar: AsyncClient) -> None:
        payload = {
            "materia_id": str(uuid.uuid4()),
            "cohorte_id": str(uuid.uuid4()),
            "tipo": "Examen",
            "numero": 1,
            "periodo": "2026-1",
            "fecha": "2026-04-15T10:00:00Z",
            "titulo": "Examen",
        }
        response = await client_gestionar.post(self.BASE, json=payload)
        assert response.status_code == 422

    async def test_extra_field_rejected_422(self, client_gestionar: AsyncClient) -> None:
        payload = {
            "materia_id": str(uuid.uuid4()),
            "cohorte_id": str(uuid.uuid4()),
            "tipo": "Parcial",
            "numero": 1,
            "periodo": "2026-1",
            "fecha": "2026-04-15T10:00:00Z",
            "titulo": "P1",
            "extra": "no",
        }
        response = await client_gestionar.post(self.BASE, json=payload)
        assert response.status_code == 422

    async def test_list_sin_permiso_retorna_403(self, client_no_perm: AsyncClient) -> None:
        response = await client_no_perm.get(self.BASE)
        assert response.status_code == 403

    async def test_get_sin_token_retorna_401(self, client: AsyncClient) -> None:
        response = await client.get(f"{self.BASE}/calendario")
        assert response.status_code == 401

    async def test_numero_negativo_rejected_422(self, client_gestionar: AsyncClient) -> None:
        payload = {
            "materia_id": str(uuid.uuid4()),
            "cohorte_id": str(uuid.uuid4()),
            "tipo": "Parcial",
            "numero": 0,
            "periodo": "2026-1",
            "fecha": "2026-04-15T10:00:00Z",
            "titulo": "P1",
        }
        response = await client_gestionar.post(self.BASE, json=payload)
        assert response.status_code == 422

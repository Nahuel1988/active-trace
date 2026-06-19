"""Tests for estructura router permission guards and basic validation.

Follows the same approach as test_rbac_endpoints: override get_current_user
and patch PermissionService.verify_permission to return grant or None.
"""

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
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def _mock_user():
    user = MagicMock()
    user.id = uuid.uuid4()
    user.tenant_id = uuid.uuid4()
    return user


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
async def client_with_perm(app, _mock_user):
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


class TestEstructuraEndpoints:
    async def test_listar_carreras_sin_token_retorna_401(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/estructura/carreras")
        assert response.status_code == 401

    async def test_listar_carreras_sin_permiso_retorna_403(self, client_no_perm: AsyncClient) -> None:
        response = await client_no_perm.get("/api/v1/estructura/carreras")
        assert response.status_code == 403

    async def test_crear_carrera_extra_field_retorna_422(self, client_with_perm: AsyncClient) -> None:
        response = await client_with_perm.post(
            "/api/v1/estructura/carreras",
            json={"codigo": "X", "nombre": "Test", "extra": "no"},
        )
        assert response.status_code == 422

    async def test_crear_carrera_success_or_401(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/estructura/carreras",
            json={"codigo": "X", "nombre": "Test"},
            headers={"Authorization": "Bearer token-con-permiso"},
        )
        assert response.status_code in (201, 401)

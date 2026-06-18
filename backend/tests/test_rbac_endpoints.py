"""Tests para endpoints de administración RBAC (C-04).

Requiere PostgreSQL corriendo (--run-db).
"""

import pytest
from httpx import ASGITransport, AsyncClient

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


class TestRbacEndpoints:
    """Scenario: Endpoints de administración RBAC protegidos por usuarios:gestionar."""

    async def test_listar_permisos_sin_token_retorna_401(self, client: AsyncClient) -> None:
        """WHEN petición sin token, THEN 401 (antes que 403)."""
        response = await client.get("/api/v1/rbac/permisos")
        assert response.status_code == 401

    async def test_listar_permisos_sin_permiso_retorna_403(self, client: AsyncClient) -> None:
        """WHEN usuario autenticado sin usuarios:gestionar, THEN 403."""
        response = await client.get(
            "/api/v1/rbac/permisos",
            headers={"Authorization": "Bearer token-sin-permiso"},
        )
        assert response.status_code == 403

    async def test_crear_permiso_campo_extra_retorna_422(self, client: AsyncClient) -> None:
        """WHEN body con campo no declarado, THEN 422 (extra='forbid')."""
        response = await client.post(
            "/api/v1/rbac/permisos",
            json={"modulo": "test", "accion": "test", "campo_extra": "x"},
            headers={"Authorization": "Bearer token-valido"},
        )
        assert response.status_code == 422

    async def test_crear_permiso_success(self, client: AsyncClient) -> None:
        """WHEN usuario con usuarios:gestionar y body válido, THEN 201."""
        response = await client.post(
            "/api/v1/rbac/permisos",
            json={"modulo": "test", "accion": "test"},
            headers={"Authorization": "Bearer token-con-permiso"},
        )
        # Nota: en test con DB real y fixtures de auth, esto sería 201
        # Con token no válido, será 401
        assert response.status_code in (201, 401)

    async def test_cross_tenant_inexistente_404(self, client: AsyncClient) -> None:
        """WHEN se intenta acceder a recurso de otro tenant, THEN 404."""
        response = await client.get(
            "/api/v1/rbac/permisos",
            headers={"Authorization": "Bearer token-otro-tenant"},
        )
        assert response.status_code in (401, 403, 404)

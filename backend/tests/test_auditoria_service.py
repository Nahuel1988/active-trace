"""Tests para AuditoriaService — scope por rol y combinación de filtros.

El service se prueba con mocks del repositorio para verificar la lógica
de scope sin depender de la base de datos.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest

from app.core.permissions import PermissionGrant
from app.services.auditoria_service import AuditoriaService


@pytest.fixture
def service() -> AuditoriaService:
    return AuditoriaService()


@pytest.fixture
def current_user_global() -> MagicMock:
    u = MagicMock()
    u.id = uuid4()
    u.tenant_id = uuid4()
    return u


@pytest.fixture
def current_user_propio() -> MagicMock:
    u = MagicMock()
    u.id = uuid4()
    u.tenant_id = uuid4()
    return u


@pytest.fixture
def grant_global() -> PermissionGrant:
    return PermissionGrant(code="auditoria:ver", scope="global")


@pytest.fixture
def grant_propio() -> PermissionGrant:
    return PermissionGrant(code="auditoria:ver", scope="propio")


class TestAuditoriaServiceScope:
    """Scenario: _resolve_scope_actor_id según el scope del permiso."""

    def test_scope_global_returns_none(
        self, service: AuditoriaService, current_user_global: MagicMock,
        grant_global: PermissionGrant,
    ) -> None:
        """GIVEN global scope THEN scope_actor_id = None."""
        result = service._resolve_scope_actor_id(grant_global, current_user_global)
        assert result is None

    def test_scope_propio_returns_user_id(
        self, service: AuditoriaService, current_user_propio: MagicMock,
        grant_propio: PermissionGrant,
    ) -> None:
        """GIVEN propio scope THEN scope_actor_id = user.id."""
        result = service._resolve_scope_actor_id(grant_propio, current_user_propio)
        assert result == current_user_propio.id


class TestAuditoriaServiceDelegation:
    """Scenario: los métodos del service delegan al repo con scope correcto."""

    @pytest.fixture(autouse=True)
    def mock_repo(self):
        with patch(
            "app.services.auditoria_service.AuditLogRepository"
        ) as mock:
            mock_instance = MagicMock()
            mock_instance.aggregate_acciones_por_dia = AsyncMock(return_value=[])
            mock_instance.aggregate_comunicaciones_por_docente = AsyncMock(
                return_value=[]
            )
            mock_instance.aggregate_interacciones_docente_materia = AsyncMock(
                return_value=[]
            )
            mock_instance.list_filtrado = AsyncMock(return_value=[])
            mock.return_value = mock_instance
            yield mock_instance

    async def test_service_pasa_scope_global_a_repo(
        self, service: AuditoriaService,
        current_user_global: MagicMock, grant_global: PermissionGrant,
        mock_repo: MagicMock,
    ) -> None:
        """GIVEN global scope THEN repo se llama con scope_actor_id=None."""
        await service.get_acciones_por_dia(
            tenant_id=current_user_global.tenant_id,
            session=MagicMock(),
            grant=grant_global,
            current_user=current_user_global,
        )
        mock_repo.aggregate_acciones_por_dia.assert_awaited_once()
        kwargs = mock_repo.aggregate_acciones_por_dia.await_args[1]
        assert kwargs["scope_actor_id"] is None

    async def test_service_pasa_scope_propio_a_repo(
        self, service: AuditoriaService,
        current_user_propio: MagicMock, grant_propio: PermissionGrant,
        mock_repo: MagicMock,
    ) -> None:
        """GIVEN propio scope THEN repo se llama con scope_actor_id=user.id."""
        await service.get_ultimas_acciones(
            tenant_id=current_user_propio.tenant_id,
            session=MagicMock(),
            grant=grant_propio,
            current_user=current_user_propio,
            limit=10,
        )
        mock_repo.list_filtrado.assert_awaited_once()
        kwargs = mock_repo.list_filtrado.await_args[1]
        assert kwargs["scope_actor_id"] == current_user_propio.id

    async def test_service_get_log_delega(
        self, service: AuditoriaService,
        current_user_global: MagicMock, grant_global: PermissionGrant,
        mock_repo: MagicMock,
    ) -> None:
        """GIVEN get_log THEN delega a list_filtrado."""
        mid = uuid4()
        await service.get_log(
            tenant_id=current_user_global.tenant_id,
            session=MagicMock(),
            grant=grant_global,
            current_user=current_user_global,
            materia_id=mid,
            accion="TEST",
            limit=50,
        )
        mock_repo.list_filtrado.assert_awaited_once()
        kwargs = mock_repo.list_filtrado.await_args[1]
        assert kwargs["materia_id"] == mid
        assert kwargs["accion"] == "TEST"
        assert kwargs["limit"] == 50

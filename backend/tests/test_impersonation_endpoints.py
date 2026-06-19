"""Tests para endpoints de impersonación — TDD Cycle 8.

Todos requieren PostgreSQL (``--run-db``).
"""

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.config import Settings
from app.core.database import Base
from app.core.dependencies import CurrentUser, get_current_user, get_db
from app.core.permissions import PermissionGrant

pytestmark = pytest.mark.requires_db


# ===========================================================================
# Helpers
# ===========================================================================


async def _ensure_tables(settings: Settings) -> None:
    """Create ALL tables in the test database (idempotent).

    Uses ``settings.test_database_url`` (or falls back to
    ``settings.database_url``).  ``create_all`` is idempotent — safe
    to call multiple times.
    """
    url = settings.test_database_url or settings.database_url
    async with create_async_engine(url, poolclass=NullPool).begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def _seed_tenant_and_user(
    db_session: AsyncSession,
    settings: Settings,
    tenant_factory,
    *,
    email_lookup: str | None = None,
    tenant: "Tenant | None" = None,
):
    """Create a tenant and a user, return (tenant, user).

    If *tenant* is provided, that tenant is reused instead of creating
    a new one — useful when two users must belong to the same tenant.

    Ensures all necessary tables exist first via ``_ensure_tables``.
    """
    from app.models.tenant import Tenant
    from app.models.user import User

    await _ensure_tables(settings)
    if tenant is None:
        tenant = await tenant_factory(session=db_session)
    lookup = email_lookup or uuid.uuid4().hex[:64]
    user = User(
        email_encrypted=f"enc-{uuid.uuid4().hex[:8]}",
        email_lookup=lookup,
        password_hash="$argon2id$hash",
        tenant_id=tenant.id,
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return tenant, user


# ===========================================================================
# 8.1 — POST exitoso → 200 + token con claims de impersonación
# ===========================================================================


class TestImpersonateStartSuccess:
    """Scenario: POST /api/auth/impersonate/{user_id} exitoso."""

    async def test_impersonate_start_returns_200_with_token(
        self,
        db_session: AsyncSession,
        settings: Settings,
        tenant_factory,
    ) -> None:
        """WHEN admin con permiso impersonacion:usar,
        THEN 200 + token con impersonated=True, actor_id, sub."""
        from app.main import create_app
        from app.models.user import User

        tenant, admin_user = await _seed_tenant_and_user(
            db_session, settings, tenant_factory,
        )
        _, target_user = await _seed_tenant_and_user(
            db_session, settings, tenant_factory,
            email_lookup=uuid.uuid4().hex[:64],
            tenant=tenant,  # same tenant as admin
        )

        app = create_app()
        # — Override get_db so the endpoint uses the test database
        app.dependency_overrides[get_db] = lambda: db_session

        async def mock_get_current_user() -> CurrentUser:
            return CurrentUser(
                user=admin_user,
                impersonated=False,
                actor_id=admin_user.id,
            )

        app.dependency_overrides[get_current_user] = mock_get_current_user
        grant = PermissionGrant(code="impersonacion:usar", scope="global")

        transport = ASGITransport(app=app)
        with patch(
            "app.services.permission_service.PermissionService.verify_permission",
            new=AsyncMock(return_value=grant),
        ):
            async with AsyncClient(
                transport=transport, base_url="http://test",
            ) as client:
                resp = await client.post(
                    f"/api/auth/impersonate/{target_user.id}",
                    headers={"Authorization": "Bearer test-token"},
                )

        app.dependency_overrides.clear()

        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["impersonated_user_id"] == str(target_user.id)

        # Decode token and verify claims
        from app.core.security import decode_token
        payload = decode_token(data["access_token"])
        assert payload["impersonated"] is True
        assert payload["actor_id"] == str(admin_user.id)
        assert payload["sub"] == str(target_user.id)
        assert payload["type"] == "access"


# ===========================================================================
# 8.2 — POST registra IMPERSONACION_INICIAR en audit_log
# ===========================================================================


class TestImpersonateStartAudit:
    """Scenario: POST exitoso registra en audit_log."""

    async def test_impersonate_start_logs_impersonacion_iniciar(
        self,
        db_session: AsyncSession,
        settings: Settings,
        tenant_factory,
    ) -> None:
        """WHEN impersonación exitosa,
        THEN existe registro IMPERSONACION_INICIAR con actor_id e impersonado_id."""
        from app.main import create_app
        from app.models.audit_log import AuditLog
        from app.models.user import User

        tenant, admin_user = await _seed_tenant_and_user(
            db_session, settings, tenant_factory,
        )
        _, target_user = await _seed_tenant_and_user(
            db_session, settings, tenant_factory,
            email_lookup=uuid.uuid4().hex[:64],
            tenant=tenant,  # same tenant as admin
        )

        app = create_app()
        app.dependency_overrides[get_db] = lambda: db_session

        async def mock_get_current_user() -> CurrentUser:
            return CurrentUser(
                user=admin_user,
                impersonated=False,
                actor_id=admin_user.id,
            )

        app.dependency_overrides[get_current_user] = mock_get_current_user
        grant = PermissionGrant(code="impersonacion:usar", scope="global")

        transport = ASGITransport(app=app)
        with patch(
            "app.services.permission_service.PermissionService.verify_permission",
            new=AsyncMock(return_value=grant),
        ):
            async with AsyncClient(
                transport=transport, base_url="http://test",
            ) as client:
                resp = await client.post(
                    f"/api/auth/impersonate/{target_user.id}",
                    headers={"Authorization": "Bearer test-token"},
                )

        app.dependency_overrides.clear()
        assert resp.status_code == 200

        # Check audit_log entry
        from sqlalchemy import select
        stmt = (
            select(AuditLog)
            .where(AuditLog.accion == "IMPERSONACION_INICIAR")
            .order_by(AuditLog.fecha_hora.desc())
            .limit(1)
        )
        result = await db_session.execute(stmt)
        entry = result.scalar_one_or_none()
        assert entry is not None, "No se encontró registro IMPERSONACION_INICIAR"
        assert entry.actor_id == admin_user.id
        assert entry.impersonado_id == target_user.id


# ===========================================================================
# 8.3 — POST sin permiso → 403
# ===========================================================================


class TestImpersonateStartForbidden:
    """Scenario: POST sin impersonacion:usar → 403."""

    async def test_impersonate_start_no_permission_returns_403(
        self,
        db_session: AsyncSession,
        settings: Settings,
        tenant_factory,
    ) -> None:
        """WHEN usuario sin impersonacion:usar,
        THEN 403."""
        from app.main import create_app
        from app.models.user import User

        tenant, admin_user = await _seed_tenant_and_user(
            db_session, settings, tenant_factory,
        )

        app = create_app()
        app.dependency_overrides[get_db] = lambda: db_session

        async def mock_get_current_user() -> CurrentUser:
            return CurrentUser(
                user=admin_user,
                impersonated=False,
            )

        app.dependency_overrides[get_current_user] = mock_get_current_user

        transport = ASGITransport(app=app)
        # verify_permission returns None → 403
        with patch(
            "app.services.permission_service.PermissionService.verify_permission",
            new=AsyncMock(return_value=None),
        ):
            async with AsyncClient(
                transport=transport, base_url="http://test",
            ) as client:
                resp = await client.post(
                    f"/api/auth/impersonate/{uuid.uuid4()}",
                    headers={"Authorization": "Bearer test-token"},
                )

        app.dependency_overrides.clear()
        assert resp.status_code == 403


# ===========================================================================
# 8.4 — POST con user_id de otro tenant → 404
# ===========================================================================


class TestImpersonateStartCrossTenant:
    """Scenario: POST con user_id de otro tenant → 404."""

    async def test_impersonate_start_other_tenant_returns_404(
        self,
        db_session: AsyncSession,
        settings: Settings,
        tenant_factory,
    ) -> None:
        """WHEN user_id no pertenece al mismo tenant del actor,
        THEN 404."""
        from app.main import create_app
        from app.models.user import User

        tenant, admin_user = await _seed_tenant_and_user(
            db_session, settings, tenant_factory,
        )
        other_tenant, other_user = await _seed_tenant_and_user(
            db_session, settings, tenant_factory,
            email_lookup=uuid.uuid4().hex[:64],
        )

        app = create_app()
        app.dependency_overrides[get_db] = lambda: db_session

        async def mock_get_current_user() -> CurrentUser:
            return CurrentUser(
                user=admin_user,
                impersonated=False,
                actor_id=admin_user.id,
            )

        app.dependency_overrides[get_current_user] = mock_get_current_user
        grant = PermissionGrant(code="impersonacion:usar", scope="global")

        transport = ASGITransport(app=app)
        with patch(
            "app.services.permission_service.PermissionService.verify_permission",
            new=AsyncMock(return_value=grant),
        ):
            async with AsyncClient(
                transport=transport, base_url="http://test",
            ) as client:
                # user from other_tenant
                resp = await client.post(
                    f"/api/auth/impersonate/{other_user.id}",
                    headers={"Authorization": "Bearer test-token"},
                )

        app.dependency_overrides.clear()
        # Other-tenant user is not found because repo.get filters by current tenant
        assert resp.status_code == 404


# ===========================================================================
# 8.5 — POST con user_id inexistente → 404
# ===========================================================================


class TestImpersonateStartNotFound:
    """Scenario: POST con user_id inexistente → 404."""

    async def test_impersonate_start_nonexistent_user_returns_404(
        self,
        db_session: AsyncSession,
        settings: Settings,
        tenant_factory,
    ) -> None:
        """WHEN user_id no existe en el sistema,
        THEN 404."""
        from app.main import create_app
        from app.models.user import User

        tenant, admin_user = await _seed_tenant_and_user(
            db_session, settings, tenant_factory,
        )

        app = create_app()
        app.dependency_overrides[get_db] = lambda: db_session

        async def mock_get_current_user() -> CurrentUser:
            return CurrentUser(
                user=admin_user,
                impersonated=False,
                actor_id=admin_user.id,
            )

        app.dependency_overrides[get_current_user] = mock_get_current_user
        grant = PermissionGrant(code="impersonacion:usar", scope="global")

        non_existent_id = uuid.uuid4()

        transport = ASGITransport(app=app)
        with patch(
            "app.services.permission_service.PermissionService.verify_permission",
            new=AsyncMock(return_value=grant),
        ):
            async with AsyncClient(
                transport=transport, base_url="http://test",
            ) as client:
                resp = await client.post(
                    f"/api/auth/impersonate/{non_existent_id}",
                    headers={"Authorization": "Bearer test-token"},
                )

        app.dependency_overrides.clear()
        assert resp.status_code == 404


# ===========================================================================
# 8.6 — POST con propio user_id → 400
# ===========================================================================


class TestImpersonateStartSelf:
    """Scenario: POST con propio user_id → 400."""

    async def test_impersonate_start_self_returns_400(
        self,
        db_session: AsyncSession,
        settings: Settings,
        tenant_factory,
    ) -> None:
        """WHEN usuario intenta impersonarse a sí mismo,
        THEN 400."""
        from app.main import create_app
        from app.models.user import User

        tenant, admin_user = await _seed_tenant_and_user(
            db_session, settings, tenant_factory,
        )

        app = create_app()
        app.dependency_overrides[get_db] = lambda: db_session

        async def mock_get_current_user() -> CurrentUser:
            return CurrentUser(
                user=admin_user,
                impersonated=False,
                actor_id=admin_user.id,
            )

        app.dependency_overrides[get_current_user] = mock_get_current_user
        grant = PermissionGrant(code="impersonacion:usar", scope="global")

        transport = ASGITransport(app=app)
        with patch(
            "app.services.permission_service.PermissionService.verify_permission",
            new=AsyncMock(return_value=grant),
        ):
            async with AsyncClient(
                transport=transport, base_url="http://test",
            ) as client:
                resp = await client.post(
                    f"/api/auth/impersonate/{admin_user.id}",
                    headers={"Authorization": "Bearer test-token"},
                )

        app.dependency_overrides.clear()
        assert resp.status_code == 400


# ===========================================================================
# 8.7 — DELETE con token de impersonación → 204 + IMPERSONACION_FINALIZAR
# ===========================================================================


class TestImpersonateEndSuccess:
    """Scenario: DELETE /api/auth/impersonate con token de impersonación."""

    async def test_impersonate_end_with_impersonation_token_returns_204(
        self,
        db_session: AsyncSession,
        settings: Settings,
        tenant_factory,
    ) -> None:
        """WHEN DELETE con token impersonado,
        THEN 204 + registro IMPERSONACION_FINALIZAR."""
        from app.main import create_app
        from app.models.audit_log import AuditLog
        from app.models.user import User

        tenant, admin_user = await _seed_tenant_and_user(
            db_session, settings, tenant_factory,
        )
        _, target_user = await _seed_tenant_and_user(
            db_session, settings, tenant_factory,
            email_lookup=uuid.uuid4().hex[:64],
        )

        app = create_app()
        app.dependency_overrides[get_db] = lambda: db_session

        # This is an impersonated session
        async def mock_get_current_user() -> CurrentUser:
            return CurrentUser(
                user=target_user,
                impersonated=True,
                actor_id=admin_user.id,
            )

        app.dependency_overrides[get_current_user] = mock_get_current_user

        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://test",
        ) as client:
            resp = await client.delete(
                "/api/auth/impersonate",
                headers={"Authorization": "Bearer test-token"},
            )

        app.dependency_overrides.clear()
        assert resp.status_code == 204

        # Check audit_log entry
        from sqlalchemy import select
        stmt = (
            select(AuditLog)
            .where(AuditLog.accion == "IMPERSONACION_FINALIZAR")
            .order_by(AuditLog.fecha_hora.desc())
            .limit(1)
        )
        result = await db_session.execute(stmt)
        entry = result.scalar_one_or_none()
        assert entry is not None, "No se encontró IMPERSONACION_FINALIZAR"
        assert entry.actor_id == admin_user.id
        assert entry.impersonado_id == target_user.id


# ===========================================================================
# 8.8 — DELETE con token normal → 400
# ===========================================================================


class TestImpersonateEndNormalToken:
    """Scenario: DELETE con token normal → 400."""

    async def test_impersonate_end_with_normal_token_returns_400(
        self,
        db_session: AsyncSession,
        settings: Settings,
        tenant_factory,
    ) -> None:
        """WHEN DELETE con token sin impersonación,
        THEN 400."""
        from app.main import create_app
        from app.models.user import User

        tenant, admin_user = await _seed_tenant_and_user(
            db_session, settings, tenant_factory,
        )

        app = create_app()
        app.dependency_overrides[get_db] = lambda: db_session

        async def mock_get_current_user() -> CurrentUser:
            return CurrentUser(
                user=admin_user,
                impersonated=False,
                actor_id=admin_user.id,
            )

        app.dependency_overrides[get_current_user] = mock_get_current_user

        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://test",
        ) as client:
            resp = await client.delete(
                "/api/auth/impersonate",
                headers={"Authorization": "Bearer test-token"},
            )

        app.dependency_overrides.clear()
        assert resp.status_code == 400

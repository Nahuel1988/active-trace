"""Tests para AuditContext y audit_action helper — TDD Cycle 4.

RED: audit.py no existe → tests fallan.
GREEN: se crea audit.py con AuditContext + audit_action → tests pasan.
"""

import uuid

import pytest
from sqlalchemy import select

from app.models.audit_log import AuditLog

# Solo los tests que tocan DB necesitan requires_db
# TestAuditContext (3 tests) es puramente unitario — no necesita DB


class TestAuditContext:
    """Scenario: AuditContext se construye correctamente."""

    def test_context_has_all_fields(self) -> None:
        """WHEN AuditContext(...), THEN todos los campos están presentes."""
        from app.core.audit import AuditContext
        ctx = AuditContext(
            actor_id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            ip="10.0.0.1",
            user_agent="test-agent",
        )
        assert ctx.actor_id is not None
        assert ctx.tenant_id is not None
        assert ctx.ip == "10.0.0.1"
        assert ctx.user_agent == "test-agent"
        assert ctx.impersonado_id is None

    def test_context_with_impersonado(self) -> None:
        """WHEN AuditContext con impersonado_id, THEN se almacena."""
        from app.core.audit import AuditContext
        imp_id = uuid.uuid4()
        ctx = AuditContext(
            actor_id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            ip="::1",
            user_agent="test",
            impersonado_id=imp_id,
        )
        assert ctx.impersonado_id == imp_id

    def test_context_immutable_fields(self) -> None:
        """THEN AuditContext usa campos congelados (dataclass frozen)."""
        from app.core.audit import AuditContext
        ctx = AuditContext(
            actor_id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            ip="1.2.3.4",
            user_agent="test",
        )
        with pytest.raises(AttributeError):
            ctx.actor_id = uuid.uuid4()  # type: ignore[misc]


@pytest.mark.requires_db
class TestAuditAction:
    """Scenario: audit_action persiste un AuditLog completo."""

    async def test_audit_action_creates_entry(
        self,
        db_session,
        settings,
    ) -> None:
        """WHEN audit_action(ctx, accion="TEST", detalle={}), THEN registro creado."""
        from sqlalchemy import NullPool
        from sqlalchemy.ext.asyncio import create_async_engine
        from app.core.database import Base
        from app.models.tenant import Tenant
        from app.models.user import User
        from app.core.audit import AuditContext, audit_action

        url = settings.test_database_url or settings.database_url
        async with create_async_engine(url, poolclass=NullPool).begin() as conn:
            await conn.run_sync(
                Base.metadata.create_all,
                tables=[Tenant.__table__, User.__table__, AuditLog.__table__],
            )

        tenant = Tenant(id=uuid.uuid4(), slug=f"t-{uuid.uuid4().hex[:8]}", nombre="Test")
        db_session.add(tenant)
        await db_session.flush()

        user = User(
            email_encrypted="enc",
            email_lookup=uuid.uuid4().hex[:64],
            password_hash="$argon2id$hash",
            tenant_id=tenant.id,
        )
        db_session.add(user)
        await db_session.flush()

        ctx = AuditContext(
            actor_id=user.id,
            tenant_id=tenant.id,
            ip="10.0.0.1",
            user_agent="pytest",
        )
        entry = await audit_action(
            ctx=ctx,
            accion="TEST_ACTION",
            detalle={"msg": "hello"},
            filas_afectadas=5,
            session=db_session,
        )

        assert entry.id is not None
        assert entry.accion == "TEST_ACTION"
        assert entry.detalle == {"msg": "hello"}
        assert entry.filas_afectadas == 5
        assert entry.actor_id == user.id
        assert entry.impersonado_id is None

    async def test_audit_action_with_impersonado(
        self,
        db_session,
        settings,
    ) -> None:
        """WHEN audit_action con impersonado, THEN impersonado_id registrado."""
        from sqlalchemy import NullPool
        from sqlalchemy.ext.asyncio import create_async_engine
        from app.core.database import Base
        from app.models.tenant import Tenant
        from app.models.user import User
        from app.core.audit import AuditContext, audit_action

        url = settings.test_database_url or settings.database_url
        async with create_async_engine(url, poolclass=NullPool).begin() as conn:
            await conn.run_sync(
                Base.metadata.create_all,
                tables=[Tenant.__table__, User.__table__, AuditLog.__table__],
            )

        tenant = Tenant(id=uuid.uuid4(), slug=f"t-{uuid.uuid4().hex[:8]}", nombre="Test")
        db_session.add(tenant)
        await db_session.flush()

        actor = User(
            email_encrypted="enc-a",
            email_lookup=uuid.uuid4().hex[:64],
            password_hash="$argon2id$hash",
            tenant_id=tenant.id,
        )
        impersonated = User(
            email_encrypted="enc-b",
            email_lookup=uuid.uuid4().hex[:64],
            password_hash="$argon2id$hash",
            tenant_id=tenant.id,
        )
        db_session.add_all([actor, impersonated])
        await db_session.flush()

        ctx = AuditContext(
            actor_id=actor.id,
            tenant_id=tenant.id,
            ip="::1",
            user_agent="test",
            impersonado_id=impersonated.id,
        )
        entry = await audit_action(
            ctx=ctx,
            accion="IMPERSONACION_INICIAR",
            detalle={"target": str(impersonated.id)},
            session=db_session,
        )

        assert entry.actor_id == actor.id
        assert entry.impersonado_id == impersonated.id
        assert entry.accion == "IMPERSONACION_INICIAR"

    async def test_audit_action_repository_injection(
        self,
        db_session,
        settings,
    ) -> None:
        """WHEN audit_action recibe repo, THEN lo usa para persistir."""
        from sqlalchemy import NullPool
        from sqlalchemy.ext.asyncio import create_async_engine
        from app.core.database import Base
        from app.models.tenant import Tenant
        from app.models.user import User
        from app.core.audit import AuditContext, audit_action
        from app.repositories.audit_log_repository import AuditLogRepository

        url = settings.test_database_url or settings.database_url
        async with create_async_engine(url, poolclass=NullPool).begin() as conn:
            await conn.run_sync(
                Base.metadata.create_all,
                tables=[Tenant.__table__, User.__table__, AuditLog.__table__],
            )

        tenant = Tenant(id=uuid.uuid4(), slug=f"t-{uuid.uuid4().hex[:8]}", nombre="Test")
        db_session.add(tenant)
        await db_session.flush()

        user = User(
            email_encrypted="enc",
            email_lookup=uuid.uuid4().hex[:64],
            password_hash="$argon2id$hash",
            tenant_id=tenant.id,
        )
        db_session.add(user)
        await db_session.flush()

        ctx = AuditContext(
            actor_id=user.id,
            tenant_id=tenant.id,
            ip="10.0.0.1",
            user_agent="test",
        )
        repo = AuditLogRepository()
        entry = await audit_action(
            ctx=ctx,
            accion="TEST_REPO",
            detalle={},
            session=db_session,
            repo=repo,
        )
        assert entry.id is not None
        assert entry.accion == "TEST_REPO"

        # Verify it's actually in the DB
        result = await db_session.execute(
            select(AuditLog).where(AuditLog.id == entry.id)
        )
        assert result.scalar_one_or_none() is not None

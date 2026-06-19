"""Tests para AuditLogRepository — TDD Cycle 3.

RED: El repositorio no existe → tests fallan.
GREEN: Se crea el repositorio y los tests pasan.
TRIANGULATE: Aislamiento multi-tenant, sin métodos de mutación.
"""

import uuid

import pytest
from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.config import Settings
from app.core.database import Base

pytestmark = pytest.mark.requires_db


class TestAuditLogRepositoryAdd:
    """Scenario: AuditLogRepository.add persiste un registro."""

    async def test_add_persists_entry(
        self,
        db_session: AsyncSession,
        settings: Settings,
    ) -> None:
        """WHEN add(entry), THEN el registro queda persistido."""
        from app.models.tenant import Tenant
        from app.models.user import User
        from app.models.audit_log import AuditLog
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
            email_lookup="x" * 64,
            password_hash="$argon2id$hash",
            tenant_id=tenant.id,
        )
        db_session.add(user)
        await db_session.flush()

        entry = AuditLog(
            tenant_id=tenant.id,
            actor_id=user.id,
            accion="TEST_ADD",
            detalle={"msg": "hello"},
            filas_afectadas=3,
            ip="10.0.0.1",
            user_agent="pytest",
        )
        repo = AuditLogRepository()
        await repo.add(entry=entry, session=db_session)

        # Read back
        from sqlalchemy import select
        result = await db_session.execute(
            select(AuditLog).where(AuditLog.id == entry.id)
        )
        saved = result.scalar_one_or_none()
        assert saved is not None
        assert saved.accion == "TEST_ADD"
        assert saved.detalle == {"msg": "hello"}
        assert saved.filas_afectadas == 3
        assert saved.ip == "10.0.0.1"

    async def test_add_returns_entry_with_id(
        self,
        db_session: AsyncSession,
        settings: Settings,
    ) -> None:
        """WHEN add(entry), THEN retorna la entry con id generado."""
        from app.models.tenant import Tenant
        from app.models.user import User
        from app.models.audit_log import AuditLog
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
            email_lookup="y" * 64,
            password_hash="$argon2id$hash",
            tenant_id=tenant.id,
        )
        db_session.add(user)
        await db_session.flush()

        entry = AuditLog(
            tenant_id=tenant.id,
            actor_id=user.id,
            accion="TEST_ADD_RETURN",
            detalle={},
            ip="::1",
            user_agent="test",
        )
        repo = AuditLogRepository()
        saved = await repo.add(entry=entry, session=db_session)
        assert saved.id is not None
        assert saved.accion == "TEST_ADD_RETURN"


class TestAuditLogRepositoryList:
    """Scenario: AuditLogRepository.list con scope-tenant."""

    async def test_list_returns_tenant_entries(
        self,
        db_session: AsyncSession,
        settings: Settings,
    ) -> None:
        """WHEN list(tenant_id=X), THEN solo entradas de X."""
        from app.models.tenant import Tenant
        from app.models.user import User
        from app.models.audit_log import AuditLog
        from app.repositories.audit_log_repository import AuditLogRepository

        url = settings.test_database_url or settings.database_url
        async with create_async_engine(url, poolclass=NullPool).begin() as conn:
            await conn.run_sync(
                Base.metadata.create_all,
                tables=[Tenant.__table__, User.__table__, AuditLog.__table__],
            )

        tenant_a = Tenant(id=uuid.uuid4(), slug=f"a-{uuid.uuid4().hex[:8]}", nombre="A")
        tenant_b = Tenant(id=uuid.uuid4(), slug=f"b-{uuid.uuid4().hex[:8]}", nombre="B")
        db_session.add_all([tenant_a, tenant_b])
        await db_session.flush()

        user_a = User(
            email_encrypted="enc-a",
            email_lookup="a" * 64,
            password_hash="$argon2id$hash",
            tenant_id=tenant_a.id,
        )
        user_b = User(
            email_encrypted="enc-b",
            email_lookup="b" * 64,
            password_hash="$argon2id$hash",
            tenant_id=tenant_b.id,
        )
        db_session.add_all([user_a, user_b])
        await db_session.flush()

        entry_a = AuditLog(
            tenant_id=tenant_a.id, actor_id=user_a.id,
            accion="ACTION_A", detalle={}, ip="1", user_agent="t",
        )
        entry_b = AuditLog(
            tenant_id=tenant_b.id, actor_id=user_b.id,
            accion="ACTION_B", detalle={}, ip="2", user_agent="t",
        )
        db_session.add_all([entry_a, entry_b])
        await db_session.flush()

        repo = AuditLogRepository()
        result_a = await repo.list(tenant_id=tenant_a.id, session=db_session)
        result_b = await repo.list(tenant_id=tenant_b.id, session=db_session)

        ids_a = [r.id for r in result_a]
        ids_b = [r.id for r in result_b]

        assert entry_a.id in ids_a
        assert entry_b.id not in ids_a
        assert entry_b.id in ids_b
        assert entry_a.id not in ids_b

    async def test_list_respects_limit(
        self,
        db_session: AsyncSession,
        settings: Settings,
    ) -> None:
        """WHEN list con limit, THEN respeta el límite."""
        from app.models.tenant import Tenant
        from app.models.user import User
        from app.models.audit_log import AuditLog
        from app.repositories.audit_log_repository import AuditLogRepository

        url = settings.test_database_url or settings.database_url
        async with create_async_engine(url, poolclass=NullPool).begin() as conn:
            await conn.run_sync(
                Base.metadata.create_all,
                tables=[Tenant.__table__, User.__table__, AuditLog.__table__],
            )

        tenant = Tenant(id=uuid.uuid4(), slug=f"t-{uuid.uuid4().hex[:8]}", nombre="T")
        db_session.add(tenant)
        await db_session.flush()

        user = User(
            email_encrypted="enc",
            email_lookup="z" * 64,
            password_hash="$argon2id$hash",
            tenant_id=tenant.id,
        )
        db_session.add(user)
        await db_session.flush()

        for i in range(5):
            db_session.add(AuditLog(
                tenant_id=tenant.id, actor_id=user.id,
                accion=f"ACT_{i}", detalle={}, ip="1", user_agent="t",
            ))
        await db_session.flush()

        repo = AuditLogRepository()
        result = await repo.list(tenant_id=tenant.id, session=db_session, limit=3)
        assert len(result) == 3


class TestAuditLogRepositoryNoMutation:
    """Scenario: El repositorio NO expone métodos de mutación."""

    def test_mutation_methods_raise(self) -> None:
        """THEN métodos de mutación lanzan NotImplementedError."""
        import pytest
        from app.repositories.audit_log_repository import AuditLogRepository
        repo = AuditLogRepository()
        with pytest.raises(NotImplementedError):
            repo.update()
        with pytest.raises(NotImplementedError):
            repo.soft_delete()
        # BaseRepository no expone delete() como método público
        assert not hasattr(repo, "delete"), "AuditLogRepository no debe tener delete()"

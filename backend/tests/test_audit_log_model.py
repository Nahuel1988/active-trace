"""Tests para el modelo AuditLog — TDD Cycle 2.

RED: El modelo no existe → tests fallan.
GREEN: Se crea el modelo y los tests pasan.
"""

import uuid

import pytest
from sqlalchemy import NullPool, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.config import Settings
from app.core.database import Base

pytestmark = pytest.mark.requires_db


class TestAuditLogModel:
    """Scenario: Modelo AuditLog persiste y es inmutable."""

    async def test_audit_log_persists_with_all_fields(
        self,
        db_session: AsyncSession,
        settings: Settings,
    ) -> None:
        """WHEN se crea un AuditLog con todos los campos, THEN persiste correctamente."""
        from app.models.tenant import Tenant
        from app.models.user import User
        from app.models.audit_log import AuditLog

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
            email_lookup="a" * 64,
            password_hash="$argon2id$hash",
            tenant_id=tenant.id,
        )
        db_session.add(user)
        await db_session.flush()

        entry = AuditLog(
            tenant_id=tenant.id,
            actor_id=user.id,
            accion="TEST_ACTION",
            detalle={"key": "value"},
            filas_afectadas=5,
            ip="192.168.1.1",
            user_agent="test-agent",
        )
        db_session.add(entry)
        await db_session.flush()
        await db_session.refresh(entry)

        assert entry.id is not None
        assert entry.tenant_id == tenant.id
        assert entry.actor_id == user.id
        assert entry.accion == "TEST_ACTION"
        assert entry.detalle == {"key": "value"}
        assert entry.filas_afectadas == 5
        assert entry.ip == "192.168.1.1"
        assert entry.user_agent == "test-agent"
        assert entry.fecha_hora is not None
        assert entry.impersonado_id is None

    async def test_audit_log_with_impersonado_id(
        self,
        db_session: AsyncSession,
        settings: Settings,
    ) -> None:
        """WHEN impersonado_id provisto, THEN se persiste correctamente."""
        from app.models.tenant import Tenant
        from app.models.user import User
        from app.models.audit_log import AuditLog

        url = settings.test_database_url or settings.database_url
        async with create_async_engine(url, poolclass=NullPool).begin() as conn:
            await conn.run_sync(
                Base.metadata.create_all,
                tables=[Tenant.__table__, User.__table__, AuditLog.__table__],
            )

        tenant = Tenant(id=uuid.uuid4(), slug=f"t-{uuid.uuid4().hex[:8]}", nombre="Test")
        db_session.add(tenant)
        await db_session.flush()

        admin = User(
            email_encrypted="enc-admin",
            email_lookup="b" * 64,
            password_hash="$argon2id$hash",
            tenant_id=tenant.id,
        )
        target = User(
            email_encrypted="enc-target",
            email_lookup="c" * 64,
            password_hash="$argon2id$hash",
            tenant_id=tenant.id,
        )
        db_session.add_all([admin, target])
        await db_session.flush()

        entry = AuditLog(
            tenant_id=tenant.id,
            actor_id=admin.id,
            impersonado_id=target.id,
            accion="IMPERSONACION_INICIAR",
            detalle={},
            ip="10.0.0.1",
            user_agent="test",
        )
        db_session.add(entry)
        await db_session.flush()
        await db_session.refresh(entry)

        assert entry.actor_id == admin.id
        assert entry.impersonado_id == target.id

    async def test_audit_log_has_no_updated_at(
        self,
        settings: Settings,
    ) -> None:
        """THEN el modelo NO tiene columna updated_at (inmutable)."""
        from app.models.audit_log import AuditLog

        cols = [c.name for c in AuditLog.__table__.columns]
        assert "updated_at" not in cols, "AuditLog debe ser inmutable: no debe tener updated_at"
        assert "deleted_at" not in cols, "AuditLog debe ser inmutable: no debe tener deleted_at"

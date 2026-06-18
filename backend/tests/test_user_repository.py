"""Tests para UserRepository — TDD.

RED: Los tests fallan porque UserRepository no existe.
GREEN: Se implementa y los tests pasan.
TRIANGULATE: Aislamiento cross-tenant, soft-delete, inactive user.
"""

import uuid

import pytest
from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.config import Settings
from app.core.database import Base

pytestmark = pytest.mark.requires_db


class TestUserRepositoryGetByEmailLookup:
    """Scenario: get_by_email_lookup() con scope de tenant."""

    async def test_finds_user_by_email_lookup_within_tenant(
        self,
        db_session: AsyncSession,
        settings: Settings,
    ) -> None:
        """WHEN email_lookup coincide y es mismo tenant, THEN retorna el User."""
        from app.models.tenant import Tenant
        from app.models.user import User
        from app.core.security import email_lookup_hash

        url = settings.test_database_url or settings.database_url
        async with create_async_engine(url, poolclass=NullPool).begin() as conn:
            await conn.run_sync(
                Base.metadata.create_all,
                tables=[Tenant.__table__, User.__table__],
            )

        tenant = Tenant(
            id=uuid.uuid4(), slug=f"t-{uuid.uuid4().hex[:8]}", nombre="T1",
        )
        db_session.add(tenant)
        await db_session.flush()

        email_lk = email_lookup_hash("user@example.com")
        user = User(
            email_encrypted="enc_test",
            email_lookup=email_lk,
            password_hash="$argon2id$hash",
            tenant_id=tenant.id,
            is_active=True,
        )
        db_session.add(user)
        await db_session.flush()

        from app.repositories.user_repository import UserRepository

        repo = UserRepository()
        result = await repo.get_by_email_lookup(
            tenant_id=tenant.id,
            email_lookup=email_lk,
            session=db_session,
        )

        assert result is not None
        assert result.id == user.id
        assert result.email_lookup == email_lk

    async def test_same_email_lookup_different_tenant_returns_none(
        self,
        db_session: AsyncSession,
        settings: Settings,
    ) -> None:
        """WHEN mismo email_lookup pero distinto tenant, THEN retorna None."""
        from app.models.tenant import Tenant
        from app.models.user import User
        from app.core.security import email_lookup_hash

        url = settings.test_database_url or settings.database_url
        async with create_async_engine(url, poolclass=NullPool).begin() as conn:
            await conn.run_sync(
                Base.metadata.create_all,
                tables=[Tenant.__table__, User.__table__],
            )

        t1 = Tenant(
            id=uuid.uuid4(), slug=f"t1-{uuid.uuid4().hex[:8]}", nombre="T1",
        )
        t2 = Tenant(
            id=uuid.uuid4(), slug=f"t2-{uuid.uuid4().hex[:8]}", nombre="T2",
        )
        db_session.add_all([t1, t2])
        await db_session.flush()

        email_lk = email_lookup_hash("same@email.com")
        user_t2 = User(
            email_encrypted="enc_t2",
            email_lookup=email_lk,
            password_hash="$argon2id$hash",
            tenant_id=t2.id,
            is_active=True,
        )
        db_session.add(user_t2)
        await db_session.flush()

        from app.repositories.user_repository import UserRepository

        repo = UserRepository()
        result = await repo.get_by_email_lookup(
            tenant_id=t1.id,
            email_lookup=email_lk,
            session=db_session,
        )

        assert result is None

    async def test_soft_deleted_user_excluded_from_lookup(
        self,
        db_session: AsyncSession,
        settings: Settings,
    ) -> None:
        """WHEN usuario soft-deleteado, THEN get_by_email_lookup retorna None."""
        from app.models.tenant import Tenant
        from app.models.user import User
        from app.core.security import email_lookup_hash
        from sqlalchemy import func

        url = settings.test_database_url or settings.database_url
        async with create_async_engine(url, poolclass=NullPool).begin() as conn:
            await conn.run_sync(
                Base.metadata.create_all,
                tables=[Tenant.__table__, User.__table__],
            )

        tenant = Tenant(
            id=uuid.uuid4(), slug=f"t-{uuid.uuid4().hex[:8]}", nombre="Test",
        )
        db_session.add(tenant)
        await db_session.flush()

        email_lk = email_lookup_hash("deleted@user.com")
        user = User(
            email_encrypted="enc_del",
            email_lookup=email_lk,
            password_hash="$argon2id$hash",
            tenant_id=tenant.id,
            is_active=True,
            deleted_at=func.now(),
        )
        db_session.add(user)
        await db_session.flush()

        from app.repositories.user_repository import UserRepository

        repo = UserRepository()
        result = await repo.get_by_email_lookup(
            tenant_id=tenant.id,
            email_lookup=email_lk,
            session=db_session,
        )

        assert result is None


class TestUserRepositoryGetActiveByEmailLookup:
    """Scenario: get_active_by_email_lookup() — solo usuarios activos."""

    async def test_inactive_user_excluded(
        self,
        db_session: AsyncSession,
        settings: Settings,
    ) -> None:
        """WHEN usuario existe pero is_active=False, THEN retorna None."""
        from app.models.tenant import Tenant
        from app.models.user import User
        from app.core.security import email_lookup_hash

        url = settings.test_database_url or settings.database_url
        async with create_async_engine(url, poolclass=NullPool).begin() as conn:
            await conn.run_sync(
                Base.metadata.create_all,
                tables=[Tenant.__table__, User.__table__],
            )

        tenant = Tenant(
            id=uuid.uuid4(), slug=f"t-{uuid.uuid4().hex[:8]}", nombre="Test",
        )
        db_session.add(tenant)
        await db_session.flush()

        email_lk = email_lookup_hash("inactive@user.com")
        user = User(
            email_encrypted="enc_inactive",
            email_lookup=email_lk,
            password_hash="$argon2id$hash",
            tenant_id=tenant.id,
            is_active=False,
        )
        db_session.add(user)
        await db_session.flush()

        from app.repositories.user_repository import UserRepository

        repo = UserRepository()
        result = await repo.get_active_by_email_lookup(
            tenant_id=tenant.id,
            email_lookup=email_lk,
            session=db_session,
        )

        assert result is None

    async def test_active_user_found(
        self,
        db_session: AsyncSession,
        settings: Settings,
    ) -> None:
        """WHEN usuario activo y mismo tenant, THEN retorna el User."""
        from app.models.tenant import Tenant
        from app.models.user import User
        from app.core.security import email_lookup_hash

        url = settings.test_database_url or settings.database_url
        async with create_async_engine(url, poolclass=NullPool).begin() as conn:
            await conn.run_sync(
                Base.metadata.create_all,
                tables=[Tenant.__table__, User.__table__],
            )

        tenant = Tenant(
            id=uuid.uuid4(), slug=f"t-{uuid.uuid4().hex[:8]}", nombre="Test",
        )
        db_session.add(tenant)
        await db_session.flush()

        email_lk = email_lookup_hash("active@user.com")
        user = User(
            email_encrypted="enc_active",
            email_lookup=email_lk,
            password_hash="$argon2id$hash",
            tenant_id=tenant.id,
            is_active=True,
        )
        db_session.add(user)
        await db_session.flush()

        from app.repositories.user_repository import UserRepository

        repo = UserRepository()
        result = await repo.get_active_by_email_lookup(
            tenant_id=tenant.id,
            email_lookup=email_lk,
            session=db_session,
        )

        assert result is not None
        assert result.id == user.id
        assert result.is_active is True

    async def test_active_tenant_isolation(
        self,
        db_session: AsyncSession,
        settings: Settings,
    ) -> None:
        """WHEN usuario activo en tenant T2, THEN consulta en T1 retorna None."""
        from app.models.tenant import Tenant
        from app.models.user import User
        from app.core.security import email_lookup_hash

        url = settings.test_database_url or settings.database_url
        async with create_async_engine(url, poolclass=NullPool).begin() as conn:
            await conn.run_sync(
                Base.metadata.create_all,
                tables=[Tenant.__table__, User.__table__],
            )

        t1 = Tenant(
            id=uuid.uuid4(), slug=f"t1-{uuid.uuid4().hex[:8]}", nombre="T1",
        )
        t2 = Tenant(
            id=uuid.uuid4(), slug=f"t2-{uuid.uuid4().hex[:8]}", nombre="T2",
        )
        db_session.add_all([t1, t2])
        await db_session.flush()

        email_lk = email_lookup_hash("cross@tenant.com")
        user_t2 = User(
            email_encrypted="enc_t2",
            email_lookup=email_lk,
            password_hash="$argon2id$hash",
            tenant_id=t2.id,
            is_active=True,
        )
        db_session.add(user_t2)
        await db_session.flush()

        from app.repositories.user_repository import UserRepository

        repo = UserRepository()
        result = await repo.get_active_by_email_lookup(
            tenant_id=t1.id,
            email_lookup=email_lk,
            session=db_session,
        )

        assert result is None

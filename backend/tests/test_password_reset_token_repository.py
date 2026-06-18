"""Tests para PasswordResetTokenRepository — TDD.

RED: Los tests fallan porque PasswordResetTokenRepository no existe.
GREEN: Se implementa y los tests pasan.
TRIANGULATE: Aislamiento cross-tenant, mark_used.
"""

import uuid

import pytest
from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.config import Settings
from app.core.database import Base

pytestmark = pytest.mark.requires_db


class TestPasswordResetTokenRepositoryGetByHash:
    """Scenario: get_by_hash() con scope de tenant."""

    async def test_get_by_hash_returns_token(
        self,
        db_session: AsyncSession,
        settings: Settings,
    ) -> None:
        """WHEN token_hash coincide y es mismo tenant, THEN retorna el token."""
        from app.models.tenant import Tenant
        from app.models.user import User
        from app.models.password_reset_token import PasswordResetToken
        from app.core.security import hash_token

        url = settings.test_database_url or settings.database_url
        async with create_async_engine(url, poolclass=NullPool).begin() as conn:
            await conn.run_sync(
                Base.metadata.create_all,
                tables=[Tenant.__table__, User.__table__, PasswordResetToken.__table__],
            )

        tenant = Tenant(
            id=uuid.uuid4(), slug=f"t-{uuid.uuid4().hex[:8]}", nombre="Test",
        )
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

        token_raw = "reset-token-abc"
        token_hashed = hash_token(token_raw)
        prt = PasswordResetToken(
            user_id=user.id,
            token_hash=token_hashed,
            expires_at=__import__("datetime").datetime.now(
                __import__("datetime").timezone.utc,
            ),
            tenant_id=tenant.id,
        )
        db_session.add(prt)
        await db_session.flush()

        from app.repositories.password_reset_token_repository import (
            PasswordResetTokenRepository,
        )

        repo = PasswordResetTokenRepository()
        result = await repo.get_by_hash(
            token_hash=token_hashed,
            tenant_id=tenant.id,
            session=db_session,
        )

        assert result is not None
        assert result.id == prt.id
        assert result.token_hash == token_hashed

    async def test_get_by_hash_other_tenant_returns_none(
        self,
        db_session: AsyncSession,
        settings: Settings,
    ) -> None:
        """WHEN mismo hash pero distinto tenant, THEN retorna None."""
        from app.models.tenant import Tenant
        from app.models.user import User
        from app.models.password_reset_token import PasswordResetToken
        from app.core.security import hash_token

        url = settings.test_database_url or settings.database_url
        async with create_async_engine(url, poolclass=NullPool).begin() as conn:
            await conn.run_sync(
                Base.metadata.create_all,
                tables=[Tenant.__table__, User.__table__, PasswordResetToken.__table__],
            )

        t1 = Tenant(
            id=uuid.uuid4(), slug=f"t1-{uuid.uuid4().hex[:8]}", nombre="T1",
        )
        t2 = Tenant(
            id=uuid.uuid4(), slug=f"t2-{uuid.uuid4().hex[:8]}", nombre="T2",
        )
        db_session.add_all([t1, t2])
        await db_session.flush()

        user = User(
            email_encrypted="enc",
            email_lookup="a" * 64,
            password_hash="$argon2id$hash",
            tenant_id=t2.id,
        )
        db_session.add(user)
        await db_session.flush()

        token_raw = "reset-token-other-tenant"
        token_hashed = hash_token(token_raw)
        prt = PasswordResetToken(
            user_id=user.id,
            token_hash=token_hashed,
            expires_at=__import__("datetime").datetime.now(
                __import__("datetime").timezone.utc,
            ),
            tenant_id=t2.id,
        )
        db_session.add(prt)
        await db_session.flush()

        from app.repositories.password_reset_token_repository import (
            PasswordResetTokenRepository,
        )

        repo = PasswordResetTokenRepository()
        result = await repo.get_by_hash(
            token_hash=token_hashed,
            tenant_id=t1.id,
            session=db_session,
        )

        assert result is None


class TestPasswordResetTokenRepositoryMarkUsed:
    """Scenario: mark_used() marca used_at."""

    async def test_mark_used_sets_used_at(
        self,
        db_session: AsyncSession,
        settings: Settings,
    ) -> None:
        """WHEN mark_used(id, tenant_id), THEN used_at se establece."""
        from app.models.tenant import Tenant
        from app.models.user import User
        from app.models.password_reset_token import PasswordResetToken
        from app.core.security import hash_token

        url = settings.test_database_url or settings.database_url
        async with create_async_engine(url, poolclass=NullPool).begin() as conn:
            await conn.run_sync(
                Base.metadata.create_all,
                tables=[Tenant.__table__, User.__table__, PasswordResetToken.__table__],
            )

        tenant = Tenant(
            id=uuid.uuid4(), slug=f"t-{uuid.uuid4().hex[:8]}", nombre="Test",
        )
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

        prt = PasswordResetToken(
            user_id=user.id,
            token_hash=hash_token("mark-used-token"),
            expires_at=__import__("datetime").datetime.now(
                __import__("datetime").timezone.utc,
            ),
            tenant_id=tenant.id,
        )
        db_session.add(prt)
        await db_session.flush()
        prt_id = prt.id

        from app.repositories.password_reset_token_repository import (
            PasswordResetTokenRepository,
        )

        repo = PasswordResetTokenRepository()
        ok = await repo.mark_used(id=prt_id, tenant_id=tenant.id, session=db_session)

        assert ok is True
        await db_session.refresh(prt)
        assert prt.used_at is not None

    async def test_mark_used_other_tenant_returns_false(
        self,
        db_session: AsyncSession,
        settings: Settings,
    ) -> None:
        """WHEN mark_used en tenant equivocado, THEN retorna False."""
        from app.models.tenant import Tenant
        from app.models.user import User
        from app.models.password_reset_token import PasswordResetToken
        from app.core.security import hash_token

        url = settings.test_database_url or settings.database_url
        async with create_async_engine(url, poolclass=NullPool).begin() as conn:
            await conn.run_sync(
                Base.metadata.create_all,
                tables=[Tenant.__table__, User.__table__, PasswordResetToken.__table__],
            )

        t1 = Tenant(
            id=uuid.uuid4(), slug=f"t1-{uuid.uuid4().hex[:8]}", nombre="T1",
        )
        t2 = Tenant(
            id=uuid.uuid4(), slug=f"t2-{uuid.uuid4().hex[:8]}", nombre="T2",
        )
        db_session.add_all([t1, t2])
        await db_session.flush()

        user = User(
            email_encrypted="enc",
            email_lookup="a" * 64,
            password_hash="$argon2id$hash",
            tenant_id=t2.id,
        )
        db_session.add(user)
        await db_session.flush()

        prt = PasswordResetToken(
            user_id=user.id,
            token_hash=hash_token("other-tenant-prt"),
            expires_at=__import__("datetime").datetime.now(
                __import__("datetime").timezone.utc,
            ),
            tenant_id=t2.id,
        )
        db_session.add(prt)
        await db_session.flush()

        from app.repositories.password_reset_token_repository import (
            PasswordResetTokenRepository,
        )

        repo = PasswordResetTokenRepository()
        ok = await repo.mark_used(id=prt.id, tenant_id=t1.id, session=db_session)

        assert ok is False

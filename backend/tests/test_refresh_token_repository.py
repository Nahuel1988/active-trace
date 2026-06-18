"""Tests para RefreshTokenRepository — TDD.

RED: Los tests fallan porque RefreshTokenRepository no existe.
GREEN: Se implementa y los tests pasan.
TRIANGULATE: Aislamiento cross-tenant, revoke_family.
"""

import uuid

import pytest
from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.config import Settings
from app.core.database import Base

pytestmark = pytest.mark.requires_db


class TestRefreshTokenRepositoryGetByHash:
    """Scenario: get_by_hash() con scope de tenant."""

    async def test_get_by_hash_finds_token_within_tenant(
        self,
        db_session: AsyncSession,
        settings: Settings,
    ) -> None:
        """WHEN token_hash coincide y es mismo tenant, THEN retorna el RefreshToken."""
        from app.models.tenant import Tenant
        from app.models.user import User
        from app.models.refresh_token import RefreshToken
        from app.core.security import hash_token

        url = settings.test_database_url or settings.database_url
        async with create_async_engine(url, poolclass=NullPool).begin() as conn:
            await conn.run_sync(
                Base.metadata.create_all,
                tables=[Tenant.__table__, User.__table__, RefreshToken.__table__],
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

        token_raw = "test-refresh-token-123"
        token_hashed = hash_token(token_raw)
        rt = RefreshToken(
            user_id=user.id,
            token_hash=token_hashed,
            family_id=uuid.uuid4(),
            expires_at=__import__("datetime").datetime.now(
                __import__("datetime").timezone.utc,
            ),
            tenant_id=tenant.id,
        )
        db_session.add(rt)
        await db_session.flush()

        from app.repositories.refresh_token_repository import RefreshTokenRepository

        repo = RefreshTokenRepository()
        result = await repo.get_by_hash(
            token_hash=token_hashed,
            tenant_id=tenant.id,
            session=db_session,
        )

        assert result is not None
        assert result.id == rt.id
        assert result.token_hash == token_hashed

    async def test_get_by_hash_other_tenant_returns_none(
        self,
        db_session: AsyncSession,
        settings: Settings,
    ) -> None:
        """WHEN mismo hash pero distinto tenant, THEN retorna None."""
        from app.models.tenant import Tenant
        from app.models.user import User
        from app.models.refresh_token import RefreshToken
        from app.core.security import hash_token

        url = settings.test_database_url or settings.database_url
        async with create_async_engine(url, poolclass=NullPool).begin() as conn:
            await conn.run_sync(
                Base.metadata.create_all,
                tables=[Tenant.__table__, User.__table__, RefreshToken.__table__],
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

        token_raw = "refresh-token-other-tenant"
        token_hashed = hash_token(token_raw)
        rt = RefreshToken(
            user_id=user.id,
            token_hash=token_hashed,
            family_id=uuid.uuid4(),
            expires_at=__import__("datetime").datetime.now(
                __import__("datetime").timezone.utc,
            ),
            tenant_id=t2.id,
        )
        db_session.add(rt)
        await db_session.flush()

        from app.repositories.refresh_token_repository import RefreshTokenRepository

        repo = RefreshTokenRepository()
        result = await repo.get_by_hash(
            token_hash=token_hashed,
            tenant_id=t1.id,
            session=db_session,
        )

        assert result is None


class TestRefreshTokenRepositoryRevoke:
    """Scenario: revoke() marca como revocado."""

    async def test_revoke_sets_revoked_at(
        self,
        db_session: AsyncSession,
        settings: Settings,
    ) -> None:
        """WHEN revoke(id, tenant), THEN revoked_at se establece."""
        from app.models.tenant import Tenant
        from app.models.user import User
        from app.models.refresh_token import RefreshToken
        from app.core.security import hash_token

        url = settings.test_database_url or settings.database_url
        async with create_async_engine(url, poolclass=NullPool).begin() as conn:
            await conn.run_sync(
                Base.metadata.create_all,
                tables=[Tenant.__table__, User.__table__, RefreshToken.__table__],
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

        token_raw = "revoke-me"
        rt = RefreshToken(
            user_id=user.id,
            token_hash=hash_token(token_raw),
            family_id=uuid.uuid4(),
            expires_at=__import__("datetime").datetime.now(
                __import__("datetime").timezone.utc,
            ),
            tenant_id=tenant.id,
        )
        db_session.add(rt)
        await db_session.flush()
        rt_id = rt.id

        from app.repositories.refresh_token_repository import RefreshTokenRepository

        repo = RefreshTokenRepository()
        ok = await repo.revoke(id=rt_id, tenant_id=tenant.id, session=db_session)

        assert ok is True
        # Verificar que revoked_at se seteó
        await db_session.refresh(rt)
        assert rt.revoked_at is not None

    async def test_revoke_other_tenant_returns_false(
        self,
        db_session: AsyncSession,
        settings: Settings,
    ) -> None:
        """WHEN revoke(id, tenant_id=t1) pero token pertenece a t2, THEN False."""
        from app.models.tenant import Tenant
        from app.models.user import User
        from app.models.refresh_token import RefreshToken
        from app.core.security import hash_token

        url = settings.test_database_url or settings.database_url
        async with create_async_engine(url, poolclass=NullPool).begin() as conn:
            await conn.run_sync(
                Base.metadata.create_all,
                tables=[Tenant.__table__, User.__table__, RefreshToken.__table__],
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

        rt = RefreshToken(
            user_id=user.id,
            token_hash=hash_token("other-tenant-token"),
            family_id=uuid.uuid4(),
            expires_at=__import__("datetime").datetime.now(
                __import__("datetime").timezone.utc,
            ),
            tenant_id=t2.id,
        )
        db_session.add(rt)
        await db_session.flush()

        from app.repositories.refresh_token_repository import RefreshTokenRepository

        repo = RefreshTokenRepository()
        ok = await repo.revoke(id=rt.id, tenant_id=t1.id, session=db_session)

        assert ok is False


class TestRefreshTokenRepositoryRevokeFamily:
    """Scenario: revoke_family() revoca todos los tokens de una familia."""

    async def test_revoke_family_revokes_all_members(
        self,
        db_session: AsyncSession,
        settings: Settings,
    ) -> None:
        """WHEN revoke_family(family_id), THEN todos los tokens quedan revocados."""
        from app.models.tenant import Tenant
        from app.models.user import User
        from app.models.refresh_token import RefreshToken
        from app.core.security import hash_token

        url = settings.test_database_url or settings.database_url
        async with create_async_engine(url, poolclass=NullPool).begin() as conn:
            await conn.run_sync(
                Base.metadata.create_all,
                tables=[Tenant.__table__, User.__table__, RefreshToken.__table__],
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

        family = uuid.uuid4()
        for i in range(3):
            rt = RefreshToken(
                user_id=user.id,
                token_hash=hash_token(f"family-token-{i}"),
                family_id=family,
                expires_at=__import__("datetime").datetime.now(
                    __import__("datetime").timezone.utc,
                ),
                tenant_id=tenant.id,
            )
            db_session.add(rt)
        await db_session.flush()

        from app.repositories.refresh_token_repository import RefreshTokenRepository

        repo = RefreshTokenRepository()
        count = await repo.revoke_family(
            family_id=family,
            tenant_id=tenant.id,
            session=db_session,
        )

        assert count == 3

        # Verificar que todos están revocados
        from sqlalchemy import select

        stmt = select(RefreshToken).where(
            RefreshToken.family_id == family,
            RefreshToken.tenant_id == tenant.id,
        )
        result = await db_session.execute(stmt)
        tokens = result.scalars().all()
        assert all(t.revoked_at is not None for t in tokens)

    async def test_revoke_family_other_tenant_not_affected(
        self,
        db_session: AsyncSession,
        settings: Settings,
    ) -> None:
        """WHEN revoke_family en t1, THEN tokens de t2 no se revocan."""
        from app.models.tenant import Tenant
        from app.models.user import User
        from app.models.refresh_token import RefreshToken
        from app.core.security import hash_token

        url = settings.test_database_url or settings.database_url
        async with create_async_engine(url, poolclass=NullPool).begin() as conn:
            await conn.run_sync(
                Base.metadata.create_all,
                tables=[Tenant.__table__, User.__table__, RefreshToken.__table__],
            )

        t1 = Tenant(
            id=uuid.uuid4(), slug=f"t1-{uuid.uuid4().hex[:8]}", nombre="T1",
        )
        t2 = Tenant(
            id=uuid.uuid4(), slug=f"t2-{uuid.uuid4().hex[:8]}", nombre="T2",
        )
        db_session.add_all([t1, t2])
        await db_session.flush()

        user1 = User(
            email_encrypted="enc1",
            email_lookup="a" * 64,
            password_hash="$argon2id$hash",
            tenant_id=t1.id,
        )
        user2 = User(
            email_encrypted="enc2",
            email_lookup="b" * 64,
            password_hash="$argon2id$hash",
            tenant_id=t2.id,
        )
        db_session.add_all([user1, user2])
        await db_session.flush()

        family = uuid.uuid4()
        rt_t1 = RefreshToken(
            user_id=user1.id,
            token_hash=hash_token("t1-token"),
            family_id=family,
            expires_at=__import__("datetime").datetime.now(
                __import__("datetime").timezone.utc,
            ),
            tenant_id=t1.id,
        )
        rt_t2 = RefreshToken(
            user_id=user2.id,
            token_hash=hash_token("t2-token"),
            family_id=family,
            expires_at=__import__("datetime").datetime.now(
                __import__("datetime").timezone.utc,
            ),
            tenant_id=t2.id,
        )
        db_session.add_all([rt_t1, rt_t2])
        await db_session.flush()

        from app.repositories.refresh_token_repository import RefreshTokenRepository

        repo = RefreshTokenRepository()
        count = await repo.revoke_family(
            family_id=family,
            tenant_id=t1.id,
            session=db_session,
        )

        assert count == 1  # Solo el de t1

        # Verificar que t2 no fue afectado
        await db_session.refresh(rt_t2)
        assert rt_t2.revoked_at is None

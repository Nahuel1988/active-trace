"""Tests para RefreshToken model — TDD.

RED: Tests fallan porque RefreshToken no existe.
GREEN: Se implementa y los tests pasan.
TRIANGULATE: token_hash UNIQUE constraint.
"""

import uuid

import pytest
from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.config import Settings
from app.core.database import Base

pytestmark = pytest.mark.requires_db


class TestRefreshTokenPersistence:
    """Scenario: RefreshToken persiste con tenant scope."""

    async def test_refresh_token_persists_with_tenant_scope(
        self,
        db_session: AsyncSession,
        settings: Settings,
    ) -> None:
        """WHEN se persiste un RefreshToken, THEN tiene UUID, tenant_id y timestamps."""
        from app.models.refresh_token import RefreshToken
        from app.models.user import User
        from app.models.tenant import Tenant

        url = settings.test_database_url or settings.database_url
        async with create_async_engine(url, poolclass=NullPool).begin() as conn:
            await conn.run_sync(
                Base.metadata.create_all,
                tables=[RefreshToken.__table__, User.__table__],
            )

        tenant = Tenant(
            id=uuid.uuid4(),
            slug=f"test-{uuid.uuid4().hex[:8]}",
            nombre="Test",
            activo=True,
        )
        db_session.add(tenant)
        await db_session.flush()

        user = User(
            tenant_id=tenant.id,
            email_encrypted="ct",
            email_lookup="lk",
            password_hash="ph",
        )
        db_session.add(user)
        await db_session.flush()

        from datetime import datetime, timedelta, timezone

        token_hash = uuid.uuid4().hex
        token = RefreshToken(
            tenant_id=tenant.id,
            user_id=user.id,
            token_hash=token_hash,
            family_id=uuid.uuid4(),
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        db_session.add(token)
        await db_session.commit()
        await db_session.refresh(token)

        assert token.id is not None
        assert isinstance(token.id, uuid.UUID)
        assert token.tenant_id == tenant.id
        assert token.user_id == user.id
        assert token.token_hash == token_hash
        assert token.family_id is not None
        assert token.expires_at is not None
        assert token.revoked_at is None
        assert token.created_at is not None
        assert token.updated_at is not None


class TestRefreshTokenUniqueHash:
    """Scenario: token_hash debe ser UNIQUE."""

    async def test_token_hash_unique_constraint(
        self,
        db_session: AsyncSession,
        settings: Settings,
    ) -> None:
        """WHEN mismo token_hash duplicado, THEN lanza UniqueViolation."""
        from app.models.refresh_token import RefreshToken
        from app.models.user import User
        from app.models.tenant import Tenant

        url = settings.test_database_url or settings.database_url
        async with create_async_engine(url, poolclass=NullPool).begin() as conn:
            await conn.run_sync(
                Base.metadata.create_all,
                tables=[RefreshToken.__table__, User.__table__],
            )

        tenant = Tenant(
            id=uuid.uuid4(),
            slug=f"test-{uuid.uuid4().hex[:8]}",
            nombre="Test",
            activo=True,
        )
        db_session.add(tenant)
        await db_session.flush()

        user = User(
            tenant_id=tenant.id,
            email_encrypted="ct",
            email_lookup="lk",
            password_hash="ph",
        )
        db_session.add(user)
        await db_session.flush()

        from datetime import datetime, timedelta, timezone

        collision_hash = uuid.uuid4().hex
        t1 = RefreshToken(
            tenant_id=tenant.id,
            user_id=user.id,
            token_hash=collision_hash,
            family_id=uuid.uuid4(),
            expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        )
        db_session.add(t1)
        await db_session.flush()

        t2 = RefreshToken(
            tenant_id=tenant.id,
            user_id=user.id,
            token_hash=collision_hash,
            family_id=uuid.uuid4(),
            expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        )
        db_session.add(t2)

        with pytest.raises(Exception) as excinfo:
            await db_session.flush()
        assert "unique" in str(excinfo.value).lower() or "duplic" in str(excinfo.value).lower()

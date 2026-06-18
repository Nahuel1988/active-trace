"""Tests para TokenService — TDD.

RED: Los tests fallan porque TokenService no existe.
GREEN: Se implementa el servicio y los tests pasan.
TRIANGULATE: Expiración, reuse detection, revocación, cross-tenant.
"""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.config import Settings
from app.core.database import Base
from app.core.security import decode_token, hash_token

pytestmark = pytest.mark.requires_db


# ============================================================================
# 5.1 — Token pair issuance
# ============================================================================


class TestIssueTokenPair:
    """Scenario: issue_token_pair() emite access + refresh tokens."""

    async def test_issue_token_pair_returns_valid_tokens(
        self,
        db_session: AsyncSession,
        settings: Settings,
    ) -> None:
        """WHEN issue_token_pair(user), THEN returns access + refresh tokens."""
        from app.models.tenant import Tenant
        from app.models.user import User
        from app.models.refresh_token import RefreshToken

        url = settings.test_database_url or settings.database_url
        async with create_async_engine(url, poolclass=NullPool).begin() as conn:
            await conn.run_sync(
                Base.metadata.create_all,
                tables=[Tenant.__table__, User.__table__, RefreshToken.__table__],
            )

        tenant = Tenant(
            id=uuid.uuid4(),
            slug=f"t-{uuid.uuid4().hex[:8]}",
            nombre="Test",
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

        from app.services.token_service import TokenService
        from app.repositories.refresh_token_repository import RefreshTokenRepository

        repo = RefreshTokenRepository()
        service = TokenService(refresh_token_repo=repo)
        result = await service.issue_token_pair(user=user, session=db_session)

        assert "access_token" in result
        assert "refresh_token" in result
        assert result["token_type"] == "bearer"

        # Verify access token is a valid JWT
        payload = decode_token(result["access_token"])
        assert payload["sub"] == str(user.id)
        assert payload["tenant_id"] == str(user.tenant_id)
        assert payload["type"] == "access"

        # Verify refresh token is an opaque string
        assert len(result["refresh_token"]) > 20

    async def test_issue_token_pair_persists_refresh_token(
        self,
        db_session: AsyncSession,
        settings: Settings,
    ) -> None:
        """WHEN issue_token_pair, THEN refresh token hash está en DB."""
        from app.models.tenant import Tenant
        from app.models.user import User
        from app.models.refresh_token import RefreshToken

        url = settings.test_database_url or settings.database_url
        async with create_async_engine(url, poolclass=NullPool).begin() as conn:
            await conn.run_sync(
                Base.metadata.create_all,
                tables=[Tenant.__table__, User.__table__, RefreshToken.__table__],
            )

        tenant = Tenant(
            id=uuid.uuid4(),
            slug=f"t-{uuid.uuid4().hex[:8]}",
            nombre="Test",
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

        from app.services.token_service import TokenService
        from app.repositories.refresh_token_repository import RefreshTokenRepository

        repo = RefreshTokenRepository()
        service = TokenService(refresh_token_repo=repo)
        result = await service.issue_token_pair(user=user, session=db_session)

        # Look up by hash
        token_hash = hash_token(result["refresh_token"])
        found = await repo.get_by_hash(
            token_hash=token_hash,
            tenant_id=tenant.id,
            session=db_session,
        )
        assert found is not None
        assert found.token_hash == token_hash
        assert found.user_id == user.id
        assert found.revoked_at is None

    async def test_issue_token_pair_roles_in_access_token(
        self,
        db_session: AsyncSession,
        settings: Settings,
    ) -> None:
        """WHEN roles provided, THEN aparecen en claims del JWT."""
        from app.models.tenant import Tenant
        from app.models.user import User
        from app.models.refresh_token import RefreshToken

        url = settings.test_database_url or settings.database_url
        async with create_async_engine(url, poolclass=NullPool).begin() as conn:
            await conn.run_sync(
                Base.metadata.create_all,
                tables=[Tenant.__table__, User.__table__, RefreshToken.__table__],
            )

        tenant = Tenant(
            id=uuid.uuid4(),
            slug=f"t-{uuid.uuid4().hex[:8]}",
            nombre="Test",
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

        from app.services.token_service import TokenService
        from app.repositories.refresh_token_repository import RefreshTokenRepository

        repo = RefreshTokenRepository()
        service = TokenService(refresh_token_repo=repo)
        roles = ["admin", "profesor"]
        result = await service.issue_token_pair(
            user=user,
            session=db_session,
            roles=roles,
        )

        payload = decode_token(result["access_token"])
        assert payload["roles"] == roles


# ============================================================================
# 5.2 — Refresh token rotation
# ============================================================================


class TestRotateRefresh:
    """Scenario: rotate_refresh() rota tokens refresh correctamente."""

    async def test_rotate_refresh_happy_path(
        self,
        db_session: AsyncSession,
        settings: Settings,
    ) -> None:
        """WHEN token válido, THEN emite nuevo par y revoca el viejo."""
        from app.models.tenant import Tenant
        from app.models.user import User
        from app.models.refresh_token import RefreshToken

        url = settings.test_database_url or settings.database_url
        async with create_async_engine(url, poolclass=NullPool).begin() as conn:
            await conn.run_sync(
                Base.metadata.create_all,
                tables=[Tenant.__table__, User.__table__, RefreshToken.__table__],
            )

        tenant = Tenant(
            id=uuid.uuid4(),
            slug=f"t-{uuid.uuid4().hex[:8]}",
            nombre="Test",
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

        from app.services.token_service import TokenService
        from app.repositories.refresh_token_repository import RefreshTokenRepository

        repo = RefreshTokenRepository()
        service = TokenService(refresh_token_repo=repo)

        # Issue initial pair
        pair = await service.issue_token_pair(user=user, session=db_session)
        old_refresh = pair["refresh_token"]

        # Rotate
        new_pair = await service.rotate_refresh(
            raw_token=old_refresh,
            tenant_id=tenant.id,
            session=db_session,
        )

        assert "access_token" in new_pair
        assert "refresh_token" in new_pair
        assert new_pair["token_type"] == "bearer"
        assert new_pair["refresh_token"] != old_refresh

        # Old token should be revoked
        old_hash = hash_token(old_refresh)
        old_token = await repo.get_by_hash(
            token_hash=old_hash,
            tenant_id=tenant.id,
            session=db_session,
        )
        assert old_token is not None
        assert old_token.revoked_at is not None

    async def test_rotate_refresh_expired_token_raises_401(
        self,
        db_session: AsyncSession,
        settings: Settings,
    ) -> None:
        """WHEN token expirado, THEN 401."""
        from app.models.tenant import Tenant
        from app.models.user import User
        from app.models.refresh_token import RefreshToken
        from app.core.security import generate_opaque_token

        url = settings.test_database_url or settings.database_url
        async with create_async_engine(url, poolclass=NullPool).begin() as conn:
            await conn.run_sync(
                Base.metadata.create_all,
                tables=[Tenant.__table__, User.__table__, RefreshToken.__table__],
            )

        tenant = Tenant(
            id=uuid.uuid4(),
            slug=f"t-{uuid.uuid4().hex[:8]}",
            nombre="Test",
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

        # Create an expired refresh token directly (past expiration)
        raw_token = generate_opaque_token()
        token_hash = hash_token(raw_token)
        expired_rt = RefreshToken(
            user_id=user.id,
            token_hash=token_hash,
            family_id=uuid.uuid4(),
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
            tenant_id=tenant.id,
        )
        db_session.add(expired_rt)
        await db_session.flush()

        from app.services.token_service import TokenService, AuthError
        from app.repositories.refresh_token_repository import RefreshTokenRepository

        repo = RefreshTokenRepository()
        service = TokenService(refresh_token_repo=repo)

        with pytest.raises(AuthError) as exc_info:
            await service.rotate_refresh(
                raw_token=raw_token,
                tenant_id=tenant.id,
                session=db_session,
            )
        assert exc_info.value.status_code == 401
        assert "expired" in exc_info.value.detail.lower()


# ============================================================================
# 5.3 — Reuse detection
# ============================================================================


class TestReuseDetection:
    """Scenario: reuse detection en rotate_refresh."""

    async def test_reuse_detected_revokes_family(
        self,
        db_session: AsyncSession,
        settings: Settings,
    ) -> None:
        """WHEN token ya rotado se presenta de nuevo,
        THEN se revoca toda la familia y se lanza 401."""
        from app.models.tenant import Tenant
        from app.models.user import User
        from app.models.refresh_token import RefreshToken

        url = settings.test_database_url or settings.database_url
        async with create_async_engine(url, poolclass=NullPool).begin() as conn:
            await conn.run_sync(
                Base.metadata.create_all,
                tables=[Tenant.__table__, User.__table__, RefreshToken.__table__],
            )

        tenant = Tenant(
            id=uuid.uuid4(),
            slug=f"t-{uuid.uuid4().hex[:8]}",
            nombre="Test",
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

        from app.services.token_service import TokenService, AuthError
        from app.repositories.refresh_token_repository import RefreshTokenRepository

        repo = RefreshTokenRepository()
        service = TokenService(refresh_token_repo=repo)

        # Issue initial pair
        pair = await service.issue_token_pair(user=user, session=db_session)
        old_refresh = pair["refresh_token"]

        # Rotate once — this revokes the old token
        new_pair = await service.rotate_refresh(
            raw_token=old_refresh,
            tenant_id=tenant.id,
            session=db_session,
        )
        new_refresh = new_pair["refresh_token"]

        # Reuse: present the ALREADY-ROTATED old token again
        with pytest.raises(AuthError) as exc_info:
            await service.rotate_refresh(
                raw_token=old_refresh,
                tenant_id=tenant.id,
                session=db_session,
            )
        assert exc_info.value.status_code == 401

        # After reuse, even the newly rotated token is revoked (family-wide)
        with pytest.raises(AuthError):
            await service.rotate_refresh(
                raw_token=new_refresh,
                tenant_id=tenant.id,
                session=db_session,
            )

    async def test_unknown_token_raises_401(
        self,
        db_session: AsyncSession,
        settings: Settings,
    ) -> None:
        """WHEN token no existe en DB, THEN 401."""
        from app.models.tenant import Tenant
        from app.models.refresh_token import RefreshToken

        url = settings.test_database_url or settings.database_url
        async with create_async_engine(url, poolclass=NullPool).begin() as conn:
            await conn.run_sync(
                Base.metadata.create_all,
                tables=[Tenant.__table__, RefreshToken.__table__],
            )

        tenant = Tenant(
            id=uuid.uuid4(),
            slug=f"t-{uuid.uuid4().hex[:8]}",
            nombre="Test",
        )
        db_session.add(tenant)
        await db_session.flush()

        from app.services.token_service import TokenService, AuthError
        from app.repositories.refresh_token_repository import RefreshTokenRepository

        repo = RefreshTokenRepository()
        service = TokenService(refresh_token_repo=repo)

        with pytest.raises(AuthError) as exc_info:
            await service.rotate_refresh(
                raw_token="this-token-never-existed",
                tenant_id=tenant.id,
                session=db_session,
            )
        assert exc_info.value.status_code == 401


# ============================================================================
# 5.4 — Session revocation (logout)
# ============================================================================


class TestRevokeSession:
    """Scenario: revoke_session() revoca toda la familia (logout)."""

    async def test_revoke_session_revokes_family(
        self,
        db_session: AsyncSession,
        settings: Settings,
    ) -> None:
        """WHEN revoke_session(token), THEN toda la familia queda revocada."""
        from app.models.tenant import Tenant
        from app.models.user import User
        from app.models.refresh_token import RefreshToken

        url = settings.test_database_url or settings.database_url
        async with create_async_engine(url, poolclass=NullPool).begin() as conn:
            await conn.run_sync(
                Base.metadata.create_all,
                tables=[Tenant.__table__, User.__table__, RefreshToken.__table__],
            )

        tenant = Tenant(
            id=uuid.uuid4(),
            slug=f"t-{uuid.uuid4().hex[:8]}",
            nombre="Test",
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

        from app.services.token_service import TokenService, AuthError
        from app.repositories.refresh_token_repository import RefreshTokenRepository

        repo = RefreshTokenRepository()
        service = TokenService(refresh_token_repo=repo)

        # Issue and rotate to have a family with multiple tokens
        pair1 = await service.issue_token_pair(user=user, session=db_session)
        old_refresh = pair1["refresh_token"]

        pair2 = await service.rotate_refresh(
            raw_token=old_refresh,
            tenant_id=tenant.id,
            session=db_session,
        )
        rotated_refresh = pair2["refresh_token"]

        # Revoke the entire family via the rotated token
        ok = await service.revoke_session(
            raw_token=rotated_refresh,
            tenant_id=tenant.id,
            session=db_session,
        )
        assert ok is True

        # Now neither token from the family works
        for token in [old_refresh, rotated_refresh]:
            with pytest.raises(AuthError) as exc_info:
                await service.rotate_refresh(
                    raw_token=token,
                    tenant_id=tenant.id,
                    session=db_session,
                )
            assert exc_info.value.status_code == 401

    async def test_revoke_session_unknown_token_returns_false(
        self,
        db_session: AsyncSession,
        settings: Settings,
    ) -> None:
        """WHEN token no existe, THEN revoke_session retorna False."""
        from app.models.tenant import Tenant
        from app.models.refresh_token import RefreshToken

        url = settings.test_database_url or settings.database_url
        async with create_async_engine(url, poolclass=NullPool).begin() as conn:
            await conn.run_sync(
                Base.metadata.create_all,
                tables=[Tenant.__table__, RefreshToken.__table__],
            )

        tenant = Tenant(
            id=uuid.uuid4(),
            slug=f"t-{uuid.uuid4().hex[:8]}",
            nombre="Test",
        )
        db_session.add(tenant)
        await db_session.flush()

        from app.services.token_service import TokenService
        from app.repositories.refresh_token_repository import RefreshTokenRepository

        repo = RefreshTokenRepository()
        service = TokenService(refresh_token_repo=repo)

        ok = await service.revoke_session(
            raw_token="this-token-never-existed",
            tenant_id=tenant.id,
            session=db_session,
        )
        assert ok is False

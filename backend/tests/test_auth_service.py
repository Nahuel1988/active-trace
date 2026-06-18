"""Tests para AuthService — TDD estricto.

Cubre:
- 6.1  authenticate()  — validación de credenciales (RED→GREEN→TRIANGULATE)
- 6.2  login()         — orquestación (token pair ó 2FA challenge)
"""

import uuid

import pytest
from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.config import Settings
from app.core.database import Base
from app.core.security import email_lookup_hash, hash_password

pytestmark = pytest.mark.requires_db


# ===========================================================================
# Helpers de setup
# ===========================================================================


async def _create_tables(settings: Settings, tables: list) -> None:
    """Create tables in a separate connection (DDL auto-commit)."""
    url = settings.test_database_url or settings.database_url
    async with create_async_engine(url, poolclass=NullPool).begin() as conn:
        await conn.run_sync(Base.metadata.create_all, tables=tables)


async def _make_user(
    db_session: AsyncSession,
    tenant: "Tenant",  # noqa: F821
    *,
    email: str = "user@test.com",
    password: str = "valid-password-99",
    is_active: bool = True,
    totp_enabled: bool = False,
) -> "User":  # noqa: F821
    """Create a minimal test user with pre-hashed password."""
    from app.models.user import User

    user = User(
        email_encrypted=f"enc-{uuid.uuid4().hex[:8]}",
        email_lookup=email_lookup_hash(email),
        password_hash=hash_password(password),
        tenant_id=tenant.id,
        is_active=is_active,
        totp_enabled=totp_enabled,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


# ===========================================================================
# 6.1 — authenticate(email, password, tenant_id)
# ===========================================================================


class TestAuthenticate:
    """Scenario: authenticate() valida credenciales contra la DB."""

    async def test_valid_credentials_returns_user(
        self,
        db_session: AsyncSession,
        settings: Settings,
        tenant_factory,
    ) -> None:
        """WHEN email + password OK → THEN retorna User."""
        from app.models.tenant import Tenant
        from app.models.user import User

        await _create_tables(settings, [Tenant.__table__, User.__table__])
        tenant = await tenant_factory(session=db_session)
        created = await _make_user(db_session, tenant)

        from app.services.auth_service import AuthService
        from app.repositories.user_repository import UserRepository

        service = AuthService(user_repo=UserRepository())
        result = await service.authenticate(
            email="user@test.com",
            password="valid-password-99",
            tenant_id=tenant.id,
            session=db_session,
        )

        assert result is not None
        assert result.id == created.id
        assert result.tenant_id == tenant.id
        assert result.is_active is True

    async def test_wrong_password_raises_auth_error(
        self,
        db_session: AsyncSession,
        settings: Settings,
        tenant_factory,
    ) -> None:
        """WHEN password incorrecta → THEN AuthError 401."""
        from app.models.tenant import Tenant
        from app.models.user import User

        await _create_tables(settings, [Tenant.__table__, User.__table__])
        tenant = await tenant_factory(session=db_session)
        await _make_user(db_session, tenant)

        from app.services.auth_service import AuthService
        from app.repositories.user_repository import UserRepository
        from app.services.token_service import AuthError

        service = AuthService(user_repo=UserRepository())
        with pytest.raises(AuthError) as exc:
            await service.authenticate(
                email="user@test.com",
                password="wrong-password",
                tenant_id=tenant.id,
                session=db_session,
            )
        assert exc.value.status_code == 401

    async def test_email_not_found_raises_auth_error(
        self,
        db_session: AsyncSession,
        settings: Settings,
        tenant_factory,
    ) -> None:
        """WHEN email no registrado → THEN AuthError 401."""
        from app.models.tenant import Tenant
        from app.models.user import User

        await _create_tables(settings, [Tenant.__table__, User.__table__])
        tenant = await tenant_factory(session=db_session)

        from app.services.auth_service import AuthService
        from app.repositories.user_repository import UserRepository
        from app.services.token_service import AuthError

        service = AuthService(user_repo=UserRepository())
        with pytest.raises(AuthError) as exc:
            await service.authenticate(
                email="noone@test.com",
                password="valid-password-99",
                tenant_id=tenant.id,
                session=db_session,
            )
        assert exc.value.status_code == 401

    async def test_inactive_user_raises_auth_error(
        self,
        db_session: AsyncSession,
        settings: Settings,
        tenant_factory,
    ) -> None:
        """WHEN usuario inactivo → THEN AuthError 401."""
        from app.models.tenant import Tenant
        from app.models.user import User

        await _create_tables(settings, [Tenant.__table__, User.__table__])
        tenant = await tenant_factory(session=db_session)
        await _make_user(db_session, tenant, email="inactive@test.com", is_active=False)

        from app.services.auth_service import AuthService
        from app.repositories.user_repository import UserRepository
        from app.services.token_service import AuthError

        service = AuthService(user_repo=UserRepository())
        with pytest.raises(AuthError) as exc:
            await service.authenticate(
                email="inactive@test.com",
                password="valid-password-99",
                tenant_id=tenant.id,
                session=db_session,
            )
        assert exc.value.status_code == 401

    async def test_uniform_error_message(
        self,
        db_session: AsyncSession,
        settings: Settings,
        tenant_factory,
    ) -> None:
        """THEN todos los fallos usan exactamente el MISMO detail."""
        from app.models.tenant import Tenant
        from app.models.user import User

        await _create_tables(settings, [Tenant.__table__, User.__table__])
        tenant = await tenant_factory(session=db_session)
        await _make_user(db_session, tenant, email="active@test.com")

        from app.services.auth_service import AuthService
        from app.repositories.user_repository import UserRepository
        from app.services.token_service import AuthError

        service = AuthService(user_repo=UserRepository())
        details = []

        # 1) Wrong password
        with pytest.raises(AuthError) as exc:
            await service.authenticate(
                email="active@test.com",
                password="wrong-password",
                tenant_id=tenant.id,
                session=db_session,
            )
        details.append(exc.value.detail)

        # 2) Email not found
        with pytest.raises(AuthError) as exc:
            await service.authenticate(
                email="noone@test.com",
                password="valid-password-99",
                tenant_id=tenant.id,
                session=db_session,
            )
        details.append(exc.value.detail)

        # 3) Inactive user
        await _make_user(db_session, tenant, email="disabled@test.com", is_active=False)
        with pytest.raises(AuthError) as exc:
            await service.authenticate(
                email="disabled@test.com",
                password="valid-password-99",
                tenant_id=tenant.id,
                session=db_session,
            )
        details.append(exc.value.detail)

        uniq = set(details)
        assert len(uniq) == 1, f"Mensajes NO uniformes: {details}"


# ===========================================================================
# 6.2 — login() orchestration
# ===========================================================================


class TestLogin:
    """Scenario: login() orquesta authenticate + emisión de tokens."""

    async def test_login_without_2fa_returns_token_pair(
        self,
        db_session: AsyncSession,
        settings: Settings,
        tenant_factory,
    ) -> None:
        """WHEN 2FA disabled → THEN returns TokenPair (access + refresh)."""
        from app.models.tenant import Tenant
        from app.models.user import User
        from app.models.refresh_token import RefreshToken

        await _create_tables(
            settings,
            [Tenant.__table__, User.__table__, RefreshToken.__table__],
        )
        tenant = await tenant_factory(session=db_session)
        await _make_user(db_session, tenant, totp_enabled=False)

        from app.services.auth_service import AuthService
        from app.repositories.user_repository import UserRepository
        from app.services.token_service import TokenService
        from app.repositories.refresh_token_repository import RefreshTokenRepository
        from app.services.totp_service import TotpService
        from app.repositories.totp_secret_repository import TotpSecretRepository
        from app.core.security import get_encryption_service

        auth_service = AuthService(user_repo=UserRepository())
        token_service = TokenService(refresh_token_repo=RefreshTokenRepository())
        totp_service = TotpService(
            totp_repo=TotpSecretRepository(),
            encryption_service=get_encryption_service(),
        )

        result = await auth_service.login(
            email="user@test.com",
            password="valid-password-99",
            tenant_id=tenant.id,
            totp_service=totp_service,
            token_service=token_service,
            session=db_session,
        )

        assert "access_token" in result
        assert "refresh_token" in result
        assert result.get("token_type") == "bearer"
        assert "challenge" not in result

    async def test_login_with_2fa_returns_challenge(
        self,
        db_session: AsyncSession,
        settings: Settings,
        tenant_factory,
    ) -> None:
        """WHEN 2FA enabled → THEN returns TwoFAChallenge (not token pair)."""
        from app.models.tenant import Tenant
        from app.models.user import User
        from app.models.refresh_token import RefreshToken

        await _create_tables(
            settings,
            [Tenant.__table__, User.__table__, RefreshToken.__table__],
        )
        tenant = await tenant_factory(session=db_session)
        await _make_user(db_session, tenant, totp_enabled=True)

        from app.services.auth_service import AuthService
        from app.repositories.user_repository import UserRepository
        from app.services.token_service import TokenService
        from app.repositories.refresh_token_repository import RefreshTokenRepository
        from app.services.totp_service import TotpService
        from app.repositories.totp_secret_repository import TotpSecretRepository
        from app.core.security import get_encryption_service

        auth_service = AuthService(user_repo=UserRepository())
        token_service = TokenService(refresh_token_repo=RefreshTokenRepository())
        totp_service = TotpService(
            totp_repo=TotpSecretRepository(),
            encryption_service=get_encryption_service(),
        )

        result = await auth_service.login(
            email="user@test.com",
            password="valid-password-99",
            tenant_id=tenant.id,
            totp_service=totp_service,
            token_service=token_service,
            session=db_session,
        )

        assert "challenge" in result
        assert result.get("type") == "2fa_challenge"
        assert "access_token" not in result

    async def test_login_with_wrong_password_raises_auth_error(
        self,
        db_session: AsyncSession,
        settings: Settings,
        tenant_factory,
    ) -> None:
        """WHEN bad password → THEN AuthError (no token, no challenge)."""
        from app.models.tenant import Tenant
        from app.models.user import User

        await _create_tables(settings, [Tenant.__table__, User.__table__])
        tenant = await tenant_factory(session=db_session)
        await _make_user(db_session, tenant)

        from app.services.auth_service import AuthService
        from app.repositories.user_repository import UserRepository
        from app.services.token_service import TokenService, AuthError
        from app.repositories.refresh_token_repository import RefreshTokenRepository
        from app.services.totp_service import TotpService
        from app.repositories.totp_secret_repository import TotpSecretRepository
        from app.core.security import get_encryption_service

        auth_service = AuthService(user_repo=UserRepository())
        token_service = TokenService(refresh_token_repo=RefreshTokenRepository())
        totp_service = TotpService(
            totp_repo=TotpSecretRepository(),
            encryption_service=get_encryption_service(),
        )

        with pytest.raises(AuthError):
            await auth_service.login(
                email="user@test.com",
                password="wrong-password",
                tenant_id=tenant.id,
                totp_service=totp_service,
                token_service=token_service,
                session=db_session,
            )

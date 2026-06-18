"""Tests para PasswordResetService — TDD.

RED: Los tests fallan porque PasswordResetService no existe.
GREEN: Se implementa y los tests pasan.
TRIANGULATE: email no existente, token usado, expirado, inválido, login post-reset.
"""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import NullPool, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.config import Settings
from app.core.database import Base

pytestmark = pytest.mark.requires_db


# ---------------------------------------------------------------------------
# FakeEmailSender — almacena correos en memoria para aserciones
# ---------------------------------------------------------------------------


class FakeEmailSender:
    """Email sender fake que almacena correos enviados en una lista."""

    def __init__(self) -> None:
        self.sent: list[dict] = []

    async def send(self, to: str, subject: str, body: str) -> None:
        self.sent.append({"to": to, "subject": subject, "body": body})


# ===========================================================================
# 8.1 RED → GREEN → TRIANGULATE: forgot(email)
# ===========================================================================


class TestForgot:
    """Scenario: forgot(email) — solicitud de reseteo de contraseña."""

    async def _setup_tenant_and_user(
        self,
        db_session: AsyncSession,
        settings: Settings,
        email: str = "user@example.com",
        is_active: bool = True,
    ) -> tuple:
        """Helper: crea tenant + user y retorna (tenant, user, email_lookup)."""
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
            id=uuid.uuid4(),
            slug=f"t-{uuid.uuid4().hex[:8]}",
            nombre="Test",
        )
        db_session.add(tenant)
        await db_session.flush()

        email_lk = email_lookup_hash(email)
        user = User(
            email_encrypted="enc_test",
            email_lookup=email_lk,
            password_hash="$argon2id$v=19$m=65536,t=3,p=4$...",
            tenant_id=tenant.id,
            is_active=is_active,
        )
        db_session.add(user)
        await db_session.flush()
        return tenant, user, email_lk

    # ── RED ─────────────────────────────────────────────────────────────

    async def test_forgot_with_existing_email_sends_email_and_persists_token(
        self,
        db_session: AsyncSession,
        settings: Settings,
    ) -> None:
        """GIVEN usuario activo WHEN forgot THEN token persistido y email enviado."""
        tenant, user, _ = await self._setup_tenant_and_user(db_session, settings)

        from app.models.password_reset_token import PasswordResetToken

        url = settings.test_database_url or settings.database_url
        async with create_async_engine(url, poolclass=NullPool).begin() as conn:
            await conn.run_sync(
                Base.metadata.create_all,
                tables=[PasswordResetToken.__table__],
            )

        from app.repositories.user_repository import UserRepository
        from app.repositories.password_reset_token_repository import (
            PasswordResetTokenRepository,
        )
        from app.services.password_reset_service import PasswordResetService

        fake_sender = FakeEmailSender()
        service = PasswordResetService(
            user_repo=UserRepository(),
            reset_token_repo=PasswordResetTokenRepository(),
            email_sender=fake_sender,
        )

        result = await service.forgot(
            email="user@example.com",
            tenant_id=tenant.id,
            session=db_session,
        )

        # Siempre retorna el mismo mensaje
        assert result["message"] == "If the email exists, a reset link has been sent."

        # Se envió exactamente 1 email
        assert len(fake_sender.sent) == 1
        assert fake_sender.sent[0]["to"] == "user@example.com"
        assert fake_sender.sent[0]["subject"] == "Password Reset"

        # Verificar que el token fue persistido como hash
        stmt = select(PasswordResetToken).where(
            PasswordResetToken.tenant_id == tenant.id,
            PasswordResetToken.user_id == user.id,
        )
        db_result = await db_session.execute(stmt)
        tokens = list(db_result.scalars().all())
        assert len(tokens) == 1
        assert len(tokens[0].token_hash) == 64  # SHA-256 hex
        assert tokens[0].used_at is None
        assert tokens[0].expires_at is not None

    # ── GREEN: el test de arriba pasa tras implementar ─────────────────

    # ── TRIANGULATE ─────────────────────────────────────────────────────

    async def test_forgot_with_nonexistent_email_returns_same_message(
        self,
        db_session: AsyncSession,
        settings: Settings,
    ) -> None:
        """GIVEN email no registrado WHEN forgot THEN mismo mensaje sin enviar email."""
        from app.models.tenant import Tenant
        from app.models.user import User

        url = settings.test_database_url or settings.database_url
        async with create_async_engine(url, poolclass=NullPool).begin() as conn:
            await conn.run_sync(
                Base.metadata.create_all,
                tables=[Tenant.__table__, User.__table__],
            )

        from app.repositories.user_repository import UserRepository
        from app.repositories.password_reset_token_repository import (
            PasswordResetTokenRepository,
        )
        from app.services.password_reset_service import PasswordResetService

        fake_sender = FakeEmailSender()
        service = PasswordResetService(
            user_repo=UserRepository(),
            reset_token_repo=PasswordResetTokenRepository(),
            email_sender=fake_sender,
        )

        result = await service.forgot(
            email="nonexistent@example.com",
            tenant_id=uuid.uuid4(),
            session=db_session,
        )

        assert result["message"] == "If the email exists, a reset link has been sent."
        assert len(fake_sender.sent) == 0

    async def test_forgot_token_stored_as_hash_only(
        self,
        db_session: AsyncSession,
        settings: Settings,
    ) -> None:
        """GIVEN forgot exitoso THEN token_hash NO contiene el token original."""
        tenant, user, _ = await self._setup_tenant_and_user(db_session, settings)

        from app.models.password_reset_token import PasswordResetToken

        url = settings.test_database_url or settings.database_url
        async with create_async_engine(url, poolclass=NullPool).begin() as conn:
            await conn.run_sync(
                Base.metadata.create_all,
                tables=[PasswordResetToken.__table__],
            )

        from app.repositories.user_repository import UserRepository
        from app.repositories.password_reset_token_repository import (
            PasswordResetTokenRepository,
        )
        from app.services.password_reset_service import PasswordResetService

        fake_sender = FakeEmailSender()
        service = PasswordResetService(
            user_repo=UserRepository(),
            reset_token_repo=PasswordResetTokenRepository(),
            email_sender=fake_sender,
        )

        await service.forgot(
            email="user@example.com",
            tenant_id=tenant.id,
            session=db_session,
        )

        # Obtener el raw token del email enviado
        assert len(fake_sender.sent) == 1
        body = fake_sender.sent[0]["body"]
        raw_token = body.split(": ")[-1].strip()

        # El token_hash en DB NO debe ser igual al raw token
        stmt = select(PasswordResetToken).where(
            PasswordResetToken.tenant_id == tenant.id,
            PasswordResetToken.user_id == user.id,
        )
        db_result = await db_session.execute(stmt)
        token = db_result.scalar_one()
        assert token.token_hash != raw_token

        # Verificar que el hash es SHA-256 del raw token
        from app.core.security import hash_token

        assert token.token_hash == hash_token(raw_token)


# ===========================================================================
# 8.2 RED → GREEN → TRIANGULATE: reset(token, new_password)
# ===========================================================================


class TestReset:
    """Scenario: reset(token, new_password) — ejecución del reseteo."""

    async def _setup_token(
        self,
        db_session: AsyncSession,
        settings: Settings,
        expire_offset: timedelta | None = None,
        used: bool = False,
    ) -> tuple:
        """Helper: crea tenant + user + password_reset_token.

        Returns:
            (tenant, user, raw_token, PasswordResetToken)
        """
        from app.models.tenant import Tenant
        from app.models.user import User
        from app.models.password_reset_token import PasswordResetToken
        from app.core.security import email_lookup_hash, generate_opaque_token, hash_token

        url = settings.test_database_url or settings.database_url
        async with create_async_engine(url, poolclass=NullPool).begin() as conn:
            await conn.run_sync(
                Base.metadata.create_all,
                tables=[
                    Tenant.__table__,
                    User.__table__,
                    PasswordResetToken.__table__,
                ],
            )

        tenant = Tenant(
            id=uuid.uuid4(),
            slug=f"t-{uuid.uuid4().hex[:8]}",
            nombre="Test",
        )
        db_session.add(tenant)
        await db_session.flush()

        user = User(
            email_encrypted="enc_reset",
            email_lookup=email_lookup_hash("reset@example.com"),
            password_hash="$argon2id$v=19$m=65536,t=3,p=4$OLD_HASH",
            tenant_id=tenant.id,
            is_active=True,
        )
        db_session.add(user)
        await db_session.flush()

        raw_token = generate_opaque_token()
        expires_at = datetime.now(timezone.utc) + (expire_offset or timedelta(minutes=15))

        prt = PasswordResetToken(
            user_id=user.id,
            token_hash=hash_token(raw_token),
            expires_at=expires_at,
            tenant_id=tenant.id,
            used_at=datetime.now(timezone.utc) if used else None,
        )
        db_session.add(prt)
        await db_session.flush()

        return tenant, user, raw_token, prt

    # ── RED ─────────────────────────────────────────────────────────────

    async def test_reset_with_valid_token_updates_password(
        self,
        db_session: AsyncSession,
        settings: Settings,
    ) -> None:
        """GIVEN token válido WHEN reset THEN nueva password seteada, token usado."""
        from app.repositories.user_repository import UserRepository
        from app.repositories.password_reset_token_repository import (
            PasswordResetTokenRepository,
        )
        from app.services.password_reset_service import PasswordResetService

        tenant, user, raw_token, prt = await self._setup_token(db_session, settings)

        fake_sender = FakeEmailSender()
        service = PasswordResetService(
            user_repo=UserRepository(),
            reset_token_repo=PasswordResetTokenRepository(),
            email_sender=fake_sender,
        )

        new_password = "NewSecurePass123!"
        result = await service.reset(
            token=raw_token,
            new_password=new_password,
            tenant_id=tenant.id,
            session=db_session,
        )

        assert result["message"] == "Password reset successfully."

        # Verificar que el hash de password cambió
        from app.core.security import verify_password

        await db_session.refresh(user)
        assert verify_password(new_password, user.password_hash) is True

        # Verificar que el token fue marcado como usado
        await db_session.refresh(prt)
        assert prt.used_at is not None

    # ── GREEN: el test de arriba pasa tras implementar ─────────────────

    # ── TRIANGULATE ─────────────────────────────────────────────────────

    async def test_reset_with_already_used_token_raises_400(
        self,
        db_session: AsyncSession,
        settings: Settings,
    ) -> None:
        """GIVEN token ya usado WHEN reset THEN HTTP 400."""
        from fastapi import HTTPException
        from app.repositories.user_repository import UserRepository
        from app.repositories.password_reset_token_repository import (
            PasswordResetTokenRepository,
        )
        from app.services.password_reset_service import PasswordResetService

        tenant, _user, raw_token, _prt = await self._setup_token(
            db_session, settings, used=True,
        )

        service = PasswordResetService(
            user_repo=UserRepository(),
            reset_token_repo=PasswordResetTokenRepository(),
            email_sender=FakeEmailSender(),
        )

        with pytest.raises(HTTPException) as exc:
            await service.reset(
                token=raw_token,
                new_password="NewSecurePass123!",
                tenant_id=tenant.id,
                session=db_session,
            )
        assert exc.value.status_code == 400
        assert "already been used" in exc.value.detail

    async def test_reset_with_expired_token_raises_400(
        self,
        db_session: AsyncSession,
        settings: Settings,
    ) -> None:
        """GIVEN token expirado WHEN reset THEN HTTP 400."""
        from fastapi import HTTPException
        from app.repositories.user_repository import UserRepository
        from app.repositories.password_reset_token_repository import (
            PasswordResetTokenRepository,
        )
        from app.services.password_reset_service import PasswordResetService

        tenant, _user, raw_token, _prt = await self._setup_token(
            db_session, settings, expire_offset=timedelta(minutes=-30),
        )

        service = PasswordResetService(
            user_repo=UserRepository(),
            reset_token_repo=PasswordResetTokenRepository(),
            email_sender=FakeEmailSender(),
        )

        with pytest.raises(HTTPException) as exc:
            await service.reset(
                token=raw_token,
                new_password="NewSecurePass123!",
                tenant_id=tenant.id,
                session=db_session,
            )
        assert exc.value.status_code == 400
        assert "expired" in exc.value.detail

    async def test_reset_with_invalid_token_raises_400(
        self,
        db_session: AsyncSession,
        settings: Settings,
    ) -> None:
        """GIVEN token inexistente WHEN reset THEN HTTP 400."""
        from fastapi import HTTPException
        from app.repositories.user_repository import UserRepository
        from app.repositories.password_reset_token_repository import (
            PasswordResetTokenRepository,
        )
        from app.services.password_reset_service import PasswordResetService

        tenant, _user, _raw_token, _prt = await self._setup_token(db_session, settings)

        service = PasswordResetService(
            user_repo=UserRepository(),
            reset_token_repo=PasswordResetTokenRepository(),
            email_sender=FakeEmailSender(),
        )

        with pytest.raises(HTTPException) as exc:
            await service.reset(
                token="invalid-token-that-does-not-exist",
                new_password="NewSecurePass123!",
                tenant_id=tenant.id,
                session=db_session,
            )
        assert exc.value.status_code == 400
        assert "Invalid or expired" in exc.value.detail




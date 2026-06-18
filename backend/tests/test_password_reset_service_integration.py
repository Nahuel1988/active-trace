"""Tests de integración para PasswordResetService — TDD.

8.3 TRIANGULATE: forgot → reset → login con nueva/antigua password,
revocar sesiones post-reset.
"""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import NullPool, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.config import Settings
from app.core.database import Base

pytestmark = pytest.mark.requires_db


class FakeEmailSender:
    """Email sender fake que almacena correos enviados en una lista."""

    def __init__(self) -> None:
        self.sent: list[dict] = []

    async def send(self, to: str, subject: str, body: str) -> None:
        self.sent.append({"to": to, "subject": subject, "body": body})


class TestResetIntegration:
    """Scenario: forgot → reset → login con nueva/antigua password."""

    async def test_login_with_new_password_after_reset_succeeds(
        self,
        db_session: AsyncSession,
        settings: Settings,
    ) -> None:
        """GIVEN reset completado WHEN login con nueva password THEN OK."""
        from app.models.tenant import Tenant
        from app.models.user import User
        from app.models.password_reset_token import PasswordResetToken
        from app.core.security import email_lookup_hash, hash_password, verify_password

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

        original_password = "OriginalPass123!"
        email = "login-test@example.com"
        user = User(
            email_encrypted="enc_login",
            email_lookup=email_lookup_hash(email),
            password_hash=hash_password(original_password),
            tenant_id=tenant.id,
            is_active=True,
        )
        db_session.add(user)
        await db_session.flush()

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

        # forgot → obtener token del email
        await service.forgot(email=email, tenant_id=tenant.id, session=db_session)
        assert len(fake_sender.sent) == 1
        body = fake_sender.sent[0]["body"]
        raw_token = body.split(": ")[-1].strip()

        # reset con nueva password
        new_password = "NewSecurePass456!"
        await service.reset(
            token=raw_token,
            new_password=new_password,
            tenant_id=tenant.id,
            session=db_session,
        )

        # login con nueva password → OK
        await db_session.refresh(user)
        assert verify_password(new_password, user.password_hash) is True

        # login con old password → FALLA
        assert verify_password(original_password, user.password_hash) is False

    async def test_reset_revokes_sessions(
        self,
        db_session: AsyncSession,
        settings: Settings,
    ) -> None:
        """GIVEN reset completado THEN todos los refresh tokens se revocan."""
        from app.models.tenant import Tenant
        from app.models.user import User
        from app.models.password_reset_token import PasswordResetToken
        from app.models.refresh_token import RefreshToken
        from app.core.security import email_lookup_hash, hash_password

        url = settings.test_database_url or settings.database_url
        async with create_async_engine(url, poolclass=NullPool).begin() as conn:
            await conn.run_sync(
                Base.metadata.create_all,
                tables=[
                    Tenant.__table__,
                    User.__table__,
                    PasswordResetToken.__table__,
                    RefreshToken.__table__,
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
            email_encrypted="enc_sessions",
            email_lookup=email_lookup_hash("sessions@example.com"),
            password_hash=hash_password("OldPass123!"),
            tenant_id=tenant.id,
            is_active=True,
        )
        db_session.add(user)
        await db_session.flush()

        family1 = uuid.uuid4()
        family2 = uuid.uuid4()
        from app.core.security import hash_token

        for i, family in enumerate([family1, family1, family2]):
            rt = RefreshToken(
                user_id=user.id,
                token_hash=hash_token(f"rt-session-{i}"),
                family_id=family,
                expires_at=datetime.now(timezone.utc) + timedelta(days=7),
                tenant_id=tenant.id,
            )
            db_session.add(rt)
        await db_session.flush()

        from app.repositories.user_repository import UserRepository
        from app.repositories.password_reset_token_repository import (
            PasswordResetTokenRepository,
        )
        from app.repositories.refresh_token_repository import RefreshTokenRepository
        from app.services.password_reset_service import PasswordResetService

        fake_sender = FakeEmailSender()
        service = PasswordResetService(
            user_repo=UserRepository(),
            reset_token_repo=PasswordResetTokenRepository(),
            email_sender=fake_sender,
            refresh_token_repo=RefreshTokenRepository(),
        )

        # forgot → get token
        await service.forgot(
            email="sessions@example.com",
            tenant_id=tenant.id,
            session=db_session,
        )
        assert len(fake_sender.sent) == 1
        body = fake_sender.sent[0]["body"]
        raw_token = body.split(": ")[-1].strip()

        # reset
        await service.reset(
            token=raw_token,
            new_password="NewSecurePass789!",
            tenant_id=tenant.id,
            session=db_session,
        )

        # Verificar que todos los refresh tokens están revocados
        stmt = select(RefreshToken).where(
            RefreshToken.user_id == user.id,
            RefreshToken.tenant_id == tenant.id,
        )
        db_result = await db_session.execute(stmt)
        tokens = list(db_result.scalars().all())
        assert len(tokens) == 3
        assert all(t.revoked_at is not None for t in tokens)

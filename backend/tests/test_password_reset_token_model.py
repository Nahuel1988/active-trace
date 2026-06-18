"""Tests para PasswordResetToken model — TDD.

RED: Tests fallan porque PasswordResetToken no existe.
GREEN: Se implementa y los tests pasan.
TRIANGULATE: token_hash persistido como hash, no en claro.
"""

import uuid

import pytest
from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.config import Settings
from app.core.database import Base

pytestmark = pytest.mark.requires_db


class TestPasswordResetTokenPersistence:
    """Scenario: PasswordResetToken persiste con tenant scope y token hasheado."""

    async def test_password_reset_token_persists(
        self,
        db_session: AsyncSession,
        settings: Settings,
    ) -> None:
        """WHEN se persiste un PasswordResetToken, THEN tiene UUID, tenant_id y timestamps."""
        from app.models.password_reset_token import PasswordResetToken
        from app.models.user import User
        from app.models.tenant import Tenant

        url = settings.test_database_url or settings.database_url
        async with create_async_engine(url, poolclass=NullPool).begin() as conn:
            await conn.run_sync(
                Base.metadata.create_all,
                tables=[PasswordResetToken.__table__, User.__table__],
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
        reset = PasswordResetToken(
            tenant_id=tenant.id,
            user_id=user.id,
            token_hash=token_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        db_session.add(reset)
        await db_session.commit()
        await db_session.refresh(reset)

        assert reset.id is not None
        assert isinstance(reset.id, uuid.UUID)
        assert reset.tenant_id == tenant.id
        assert reset.user_id == user.id
        assert reset.token_hash == token_hash
        assert reset.expires_at is not None
        assert reset.used_at is None
        assert reset.created_at is not None
        assert reset.updated_at is not None


class TestPasswordResetTokenHash:
    """TRIANGULATE: token_hash se persiste como hash, nunca el token en claro."""

    async def test_token_hash_does_not_contain_original_token(
        self,
        db_session: AsyncSession,
        settings: Settings,
    ) -> None:
        """WHEN token_hash guarda el hash, THEN la columna NO contiene el token original."""
        from hashlib import sha256

        from app.models.password_reset_token import PasswordResetToken
        from app.models.user import User
        from app.models.tenant import Tenant

        url = settings.test_database_url or settings.database_url
        async with create_async_engine(url, poolclass=NullPool).begin() as conn:
            await conn.run_sync(
                Base.metadata.create_all,
                tables=[PasswordResetToken.__table__, User.__table__],
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

        # Simulamos el proceso real: el token original NUNCA se persiste,
        # solo su hash SHA-256. Usamos un salt único para evitar colisiones
        # cross-session con datos persistentes en la DB.
        salt = uuid.uuid4().hex
        original_token = f"reset-token-{salt}"
        token_hash = sha256(original_token.encode()).hexdigest()

        reset = PasswordResetToken(
            tenant_id=tenant.id,
            user_id=user.id,
            token_hash=token_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        db_session.add(reset)
        await db_session.commit()

        # La columna almacenada NO contiene el token original
        assert original_token not in reset.token_hash
        # El valor almacenado es el hash, no el token
        assert reset.token_hash == token_hash
        # Verificamos que el hash sea un SHA-256 (64 chars hex)
        assert len(reset.token_hash) == 64

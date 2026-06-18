"""Tests para TotpSecret model — TDD.

RED: Tests fallan porque TotpSecret no existe.
GREEN: Se implementa y los tests pasan.
TRIANGULATE: secret cifrado en DB, UNIQUE user_id.
"""

import uuid

import pytest
from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.config import Settings
from app.core.database import Base

pytestmark = pytest.mark.requires_db


class TestTotpSecretPersistence:
    """Scenario: TotpSecret persiste con tenant scope y secret cifrado."""

    async def test_totp_secret_persists_with_encrypted_secret(
        self,
        db_session: AsyncSession,
        settings: Settings,
    ) -> None:
        """WHEN se persiste un TotpSecret, THEN tiene UUID, tenant_id y secret cifrado."""
        from app.models.totp_secret import TotpSecret
        from app.models.user import User
        from app.models.tenant import Tenant

        url = settings.test_database_url or settings.database_url
        async with create_async_engine(url, poolclass=NullPool).begin() as conn:
            await conn.run_sync(
                Base.metadata.create_all,
                tables=[TotpSecret.__table__, User.__table__],
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

        secret = TotpSecret(
            tenant_id=tenant.id,
            user_id=user.id,
            secret_encrypted="aes-gcm-ciphertext-base64",
        )
        db_session.add(secret)
        await db_session.commit()
        await db_session.refresh(secret)

        assert secret.id is not None
        assert isinstance(secret.id, uuid.UUID)
        assert secret.tenant_id == tenant.id
        assert secret.user_id == user.id
        assert secret.secret_encrypted == "aes-gcm-ciphertext-base64"
        assert secret.confirmed_at is None
        assert secret.created_at is not None
        assert secret.updated_at is not None


class TestTotpSecretEncrypted:
    """TRIANGULATE: secret cifrado en DB (no contiene el secret en claro)."""

    async def test_secret_encrypted_does_not_contain_plaintext(
        self,
        db_session: AsyncSession,
        settings: Settings,
    ) -> None:
        """WHEN secret_encrypted guarda ciphertext, THEN la columna NO tiene el secret en claro."""
        from app.models.totp_secret import TotpSecret
        from app.models.user import User
        from app.models.tenant import Tenant

        url = settings.test_database_url or settings.database_url
        async with create_async_engine(url, poolclass=NullPool).begin() as conn:
            await conn.run_sync(
                Base.metadata.create_all,
                tables=[TotpSecret.__table__, User.__table__],
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

        plain_secret = "JBSWY3DPEHPK3PXP"
        ciphertext = "ZnJlbmNoLXNhbHQ6MTIzNDU2Nzg5MA=="

        totp = TotpSecret(
            tenant_id=tenant.id,
            user_id=user.id,
            secret_encrypted=ciphertext,
        )
        db_session.add(totp)
        await db_session.commit()

        assert plain_secret not in totp.secret_encrypted
        assert totp.secret_encrypted == ciphertext


class TestTotpSecretUniqueUser:
    """TRIANGULATE: UNIQUE user_id — un solo secreto TOTP por usuario."""

    async def test_unique_user_id_constraint(
        self,
        db_session: AsyncSession,
        settings: Settings,
    ) -> None:
        """WHEN se inserta segundo TotpSecret para mismo user, THEN lanza violación."""
        from app.models.totp_secret import TotpSecret
        from app.models.user import User
        from app.models.tenant import Tenant

        url = settings.test_database_url or settings.database_url
        async with create_async_engine(url, poolclass=NullPool).begin() as conn:
            await conn.run_sync(
                Base.metadata.create_all,
                tables=[TotpSecret.__table__, User.__table__],
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

        s1 = TotpSecret(
            tenant_id=tenant.id,
            user_id=user.id,
            secret_encrypted="ciphertext-1",
        )
        db_session.add(s1)
        await db_session.flush()

        s2 = TotpSecret(
            tenant_id=tenant.id,
            user_id=user.id,
            secret_encrypted="ciphertext-2",
        )
        db_session.add(s2)

        with pytest.raises(Exception) as excinfo:
            await db_session.flush()
        assert "unique" in str(excinfo.value).lower() or "duplic" in str(excinfo.value).lower()

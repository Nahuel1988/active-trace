"""Tests para User model — TDD.

RED: Tests fallan porque User no existe.
GREEN: Se implementa User y los tests pasan.
TRIANGULATE: email cifrado, unique constraint cross-tenant.
"""

import uuid

import pytest
from sqlalchemy import NullPool, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.config import Settings
from app.core.database import Base

pytestmark = pytest.mark.requires_db


class TestUserPersistence:
    """Scenario: User persiste con UUID, tenant_id y timestamps."""

    async def test_user_has_uuid_tenant_and_timestamps(
        self,
        db_session: AsyncSession,
        settings: Settings,
    ) -> None:
        """WHEN se persiste un User, THEN tiene UUID, tenant_id y timestamps."""
        from app.models.user import User

        url = settings.test_database_url or settings.database_url
        async with create_async_engine(url, poolclass=NullPool).begin() as conn:
            await conn.run_sync(
                Base.metadata.create_all,
                tables=[User.__table__],
            )

        from app.models.tenant import Tenant

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
            email_encrypted="ciphertext-aes-gcm-base64",
            email_lookup="deterministic-hmac-sha256",
            password_hash="argon2id-hash-value",
            legajo=None,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        assert user.id is not None
        assert isinstance(user.id, uuid.UUID)
        assert user.tenant_id == tenant.id
        assert user.created_at is not None
        assert user.updated_at is not None
        assert user.is_active is True
        assert user.totp_enabled is False
        assert user.legajo is None

    async def test_user_defaults(
        self,
        db_session: AsyncSession,
        settings: Settings,
    ) -> None:
        """WHEN se crea User sin defaults explícitos, THEN is_active=True, totp_enabled=False."""
        from app.models.user import User

        url = settings.test_database_url or settings.database_url
        async with create_async_engine(url, poolclass=NullPool).begin() as conn:
            await conn.run_sync(
                Base.metadata.create_all,
                tables=[User.__table__],
            )

        from app.models.tenant import Tenant

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
        await db_session.commit()

        assert user.is_active is True
        assert user.totp_enabled is False


class TestUserFK:
    """Scenario: FK a tenant inexistente debe fallar."""

    async def test_fk_invalid_tenant_raises_integrity_error(
        self,
        db_session: AsyncSession,
        settings: Settings,
    ) -> None:
        """WHEN tenant_id no existe en tenant, THEN flush lanza IntegrityError."""
        from app.models.user import User

        url = settings.test_database_url or settings.database_url
        async with create_async_engine(url, poolclass=NullPool).begin() as conn:
            await conn.run_sync(
                Base.metadata.create_all,
                tables=[User.__table__],
            )

        fake_tenant_id = uuid.uuid4()
        user = User(
            tenant_id=fake_tenant_id,
            email_encrypted="ct",
            email_lookup="lk",
            password_hash="ph",
        )
        db_session.add(user)

        with pytest.raises(Exception) as excinfo:
            await db_session.flush()
        # PostgreSQL: ForeignKeyViolation / IntegrityError
        assert "foreign" in str(excinfo.value).lower() or "violat" in str(excinfo.value).lower()


class TestUserEncryptedEmail:
    """TRIANGULATE: email_encrypted no contiene el email en claro."""

    async def test_email_encrypted_column_does_not_contain_plaintext(
        self,
        db_session: AsyncSession,
        settings: Settings,
    ) -> None:
        """WHEN email_encrypted guarda ciphertext, THEN la columna NO tiene el email en claro."""
        from app.models.user import User

        url = settings.test_database_url or settings.database_url
        async with create_async_engine(url, poolclass=NullPool).begin() as conn:
            await conn.run_sync(
                Base.metadata.create_all,
                tables=[User.__table__],
            )

        from app.models.tenant import Tenant

        tenant = Tenant(
            id=uuid.uuid4(),
            slug=f"test-{uuid.uuid4().hex[:8]}",
            nombre="Test",
            activo=True,
        )
        db_session.add(tenant)
        await db_session.flush()

        plain_email = "estudiante@universidad.edu.ar"
        ciphertext = "aGVsbG8gdGhpcyBpcyBjaXBoZXJ0ZXh0ITo+"

        user = User(
            tenant_id=tenant.id,
            email_encrypted=ciphertext,
            email_lookup="hmac-of-email",
            password_hash="argon2id",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # La columna almacenada NO debe contener el email en claro
        assert plain_email not in user.email_encrypted
        # El ciphertext almacenado debe ser el que pasamos (el servicio de cifrado
        # se encarga de generar el ciphertext; el modelo solo lo persiste)
        assert user.email_encrypted == ciphertext


class TestUserUniqueEmailLookup:
    """TRIANGULATE: UNIQUE(tenant_id, email_lookup)."""

    async def test_same_email_lookup_same_tenant_fails(
        self,
        db_session: AsyncSession,
        settings: Settings,
    ) -> None:
        """WHEN mismo email_lookup en mismo tenant, THEN UniqueViolation."""
        from app.models.user import User

        url = settings.test_database_url or settings.database_url
        async with create_async_engine(url, poolclass=NullPool).begin() as conn:
            await conn.run_sync(
                Base.metadata.create_all,
                tables=[User.__table__],
            )

        from app.models.tenant import Tenant

        tenant = Tenant(
            id=uuid.uuid4(),
            slug=f"test-{uuid.uuid4().hex[:8]}",
            nombre="Test",
            activo=True,
        )
        db_session.add(tenant)
        await db_session.flush()

        user1 = User(
            tenant_id=tenant.id,
            email_encrypted="ct1",
            email_lookup="same-hmac",
            password_hash="ph1",
        )
        db_session.add(user1)
        await db_session.flush()

        user2 = User(
            tenant_id=tenant.id,
            email_encrypted="ct2",
            email_lookup="same-hmac",
            password_hash="ph2",
        )
        db_session.add(user2)

        with pytest.raises(Exception) as excinfo:
            await db_session.flush()
        assert "unique" in str(excinfo.value).lower() or "duplic" in str(excinfo.value).lower()

    async def test_same_email_lookup_different_tenant_ok(
        self,
        db_session: AsyncSession,
        settings: Settings,
    ) -> None:
        """WHEN mismo email_lookup en distinto tenant, THEN OK."""
        from app.models.user import User

        url = settings.test_database_url or settings.database_url
        async with create_async_engine(url, poolclass=NullPool).begin() as conn:
            await conn.run_sync(
                Base.metadata.create_all,
                tables=[User.__table__],
            )

        from app.models.tenant import Tenant

        t1 = Tenant(
            id=uuid.uuid4(),
            slug=f"t1-{uuid.uuid4().hex[:8]}",
            nombre="T1",
            activo=True,
        )
        t2 = Tenant(
            id=uuid.uuid4(),
            slug=f"t2-{uuid.uuid4().hex[:8]}",
            nombre="T2",
            activo=True,
        )
        db_session.add_all([t1, t2])
        await db_session.flush()

        user1 = User(
            tenant_id=t1.id,
            email_encrypted="ct1",
            email_lookup="same-hmac",
            password_hash="ph1",
        )
        user2 = User(
            tenant_id=t2.id,
            email_encrypted="ct2",
            email_lookup="same-hmac",
            password_hash="ph2",
        )
        db_session.add_all([user1, user2])
        await db_session.commit()

        assert user1.id is not None
        assert user2.id is not None
        assert user1.email_lookup == user2.email_lookup
        assert user1.tenant_id != user2.tenant_id

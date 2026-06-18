"""Tests para TotpSecretRepository — TDD.

RED: Los tests fallan porque TotpSecretRepository no existe.
GREEN: Se implementa y los tests pasan.
TRIANGULATE: Aislamiento cross-tenant, upsert crea/actualiza, confirm.
"""

import uuid

import pytest
from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.config import Settings
from app.core.database import Base

pytestmark = pytest.mark.requires_db


class TestTotpSecretRepositoryGetByUser:
    """Scenario: get_by_user() con scope de tenant."""

    async def test_get_by_user_returns_secret(
        self,
        db_session: AsyncSession,
        settings: Settings,
    ) -> None:
        """WHEN user_id y tenant_id coinciden, THEN retorna el TotpSecret."""
        from app.models.tenant import Tenant
        from app.models.user import User
        from app.models.totp_secret import TotpSecret

        url = settings.test_database_url or settings.database_url
        async with create_async_engine(url, poolclass=NullPool).begin() as conn:
            await conn.run_sync(
                Base.metadata.create_all,
                tables=[Tenant.__table__, User.__table__, TotpSecret.__table__],
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

        secret = TotpSecret(
            user_id=user.id,
            secret_encrypted="aes_encrypted_secret",
            tenant_id=tenant.id,
        )
        db_session.add(secret)
        await db_session.flush()

        from app.repositories.totp_secret_repository import TotpSecretRepository

        repo = TotpSecretRepository()
        result = await repo.get_by_user(
            user_id=user.id,
            tenant_id=tenant.id,
            session=db_session,
        )

        assert result is not None
        assert result.id == secret.id
        assert result.secret_encrypted == "aes_encrypted_secret"

    async def test_get_by_user_other_tenant_returns_none(
        self,
        db_session: AsyncSession,
        settings: Settings,
    ) -> None:
        """WHEN mismo user_id pero distinto tenant, THEN retorna None."""
        from app.models.tenant import Tenant
        from app.models.user import User
        from app.models.totp_secret import TotpSecret

        url = settings.test_database_url or settings.database_url
        async with create_async_engine(url, poolclass=NullPool).begin() as conn:
            await conn.run_sync(
                Base.metadata.create_all,
                tables=[Tenant.__table__, User.__table__, TotpSecret.__table__],
            )

        t1 = Tenant(
            id=uuid.uuid4(), slug=f"t1-{uuid.uuid4().hex[:8]}", nombre="T1",
        )
        t2 = Tenant(
            id=uuid.uuid4(), slug=f"t2-{uuid.uuid4().hex[:8]}", nombre="T2",
        )
        db_session.add_all([t1, t2])
        await db_session.flush()

        # El usuario vive en t2
        user = User(
            email_encrypted="enc",
            email_lookup="a" * 64,
            password_hash="$argon2id$hash",
            tenant_id=t2.id,
        )
        db_session.add(user)
        await db_session.flush()

        secret = TotpSecret(
            user_id=user.id,
            secret_encrypted="secret_t2",
            tenant_id=t2.id,
        )
        db_session.add(secret)
        await db_session.flush()

        from app.repositories.totp_secret_repository import TotpSecretRepository

        repo = TotpSecretRepository()
        result = await repo.get_by_user(
            user_id=user.id,
            tenant_id=t1.id,
            session=db_session,
        )

        assert result is None


class TestTotpSecretRepositoryUpsert:
    """Scenario: upsert() crea o actualiza el secreto TOTP."""

    async def test_upsert_creates_new_secret(
        self,
        db_session: AsyncSession,
        settings: Settings,
    ) -> None:
        """WHEN no existe secreto previo, THEN crea uno nuevo."""
        from app.models.tenant import Tenant
        from app.models.user import User
        from app.models.totp_secret import TotpSecret

        url = settings.test_database_url or settings.database_url
        async with create_async_engine(url, poolclass=NullPool).begin() as conn:
            await conn.run_sync(
                Base.metadata.create_all,
                tables=[Tenant.__table__, User.__table__, TotpSecret.__table__],
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

        from app.repositories.totp_secret_repository import TotpSecretRepository

        repo = TotpSecretRepository()
        result = await repo.upsert(
            user_id=user.id,
            tenant_id=tenant.id,
            secret_encrypted="new_secret_encrypted",
            session=db_session,
        )

        assert result is not None
        assert result.user_id == user.id
        assert result.secret_encrypted == "new_secret_encrypted"
        assert result.confirmed_at is None

    async def test_upsert_updates_existing_secret(
        self,
        db_session: AsyncSession,
        settings: Settings,
    ) -> None:
        """WHEN ya existe un secreto, THEN lo actualiza."""
        from app.models.tenant import Tenant
        from app.models.user import User
        from app.models.totp_secret import TotpSecret

        url = settings.test_database_url or settings.database_url
        async with create_async_engine(url, poolclass=NullPool).begin() as conn:
            await conn.run_sync(
                Base.metadata.create_all,
                tables=[Tenant.__table__, User.__table__, TotpSecret.__table__],
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

        original = TotpSecret(
            user_id=user.id,
            secret_encrypted="original_secret",
            tenant_id=tenant.id,
        )
        db_session.add(original)
        await db_session.flush()

        from app.repositories.totp_secret_repository import TotpSecretRepository

        repo = TotpSecretRepository()
        result = await repo.upsert(
            user_id=user.id,
            tenant_id=tenant.id,
            secret_encrypted="updated_secret",
            session=db_session,
        )

        assert result is not None
        assert result.id == original.id
        assert result.secret_encrypted == "updated_secret"
        assert result.confirmed_at is None  # Se resetea al actualizar


class TestTotpSecretRepositoryConfirm:
    """Scenario: confirm() marca confirmed_at."""

    async def test_confirm_sets_confirmed_at(
        self,
        db_session: AsyncSession,
        settings: Settings,
    ) -> None:
        """WHEN confirm(user_id, tenant_id), THEN confirmed_at se establece."""
        from app.models.tenant import Tenant
        from app.models.user import User
        from app.models.totp_secret import TotpSecret

        url = settings.test_database_url or settings.database_url
        async with create_async_engine(url, poolclass=NullPool).begin() as conn:
            await conn.run_sync(
                Base.metadata.create_all,
                tables=[Tenant.__table__, User.__table__, TotpSecret.__table__],
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

        secret = TotpSecret(
            user_id=user.id,
            secret_encrypted="secret_to_confirm",
            tenant_id=tenant.id,
        )
        db_session.add(secret)
        await db_session.flush()

        from app.repositories.totp_secret_repository import TotpSecretRepository

        repo = TotpSecretRepository()
        ok = await repo.confirm(
            user_id=user.id,
            tenant_id=tenant.id,
            session=db_session,
        )

        assert ok is True
        await db_session.refresh(secret)
        assert secret.confirmed_at is not None

    async def test_confirm_other_tenant_returns_false(
        self,
        db_session: AsyncSession,
        settings: Settings,
    ) -> None:
        """WHEN confirm en tenant equivocado, THEN retorna False."""
        from app.models.tenant import Tenant
        from app.models.user import User
        from app.models.totp_secret import TotpSecret

        url = settings.test_database_url or settings.database_url
        async with create_async_engine(url, poolclass=NullPool).begin() as conn:
            await conn.run_sync(
                Base.metadata.create_all,
                tables=[Tenant.__table__, User.__table__, TotpSecret.__table__],
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

        secret = TotpSecret(
            user_id=user.id,
            secret_encrypted="secret_t2",
            tenant_id=t2.id,
        )
        db_session.add(secret)
        await db_session.flush()

        from app.repositories.totp_secret_repository import TotpSecretRepository

        repo = TotpSecretRepository()
        ok = await repo.confirm(
            user_id=user.id,
            tenant_id=t1.id,
            session=db_session,
        )

        assert ok is False

    async def test_confirm_no_secret_returns_false(
        self,
        db_session: AsyncSession,
        settings: Settings,
    ) -> None:
        """WHEN no existe secreto para el usuario, THEN retorna False."""
        from app.models.tenant import Tenant
        from app.models.user import User
        from app.models.totp_secret import TotpSecret

        url = settings.test_database_url or settings.database_url
        async with create_async_engine(url, poolclass=NullPool).begin() as conn:
            await conn.run_sync(
                Base.metadata.create_all,
                tables=[Tenant.__table__, User.__table__, TotpSecret.__table__],
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

        from app.repositories.totp_secret_repository import TotpSecretRepository

        repo = TotpSecretRepository()
        ok = await repo.confirm(
            user_id=user.id,
            tenant_id=tenant.id,
            session=db_session,
        )

        assert ok is False

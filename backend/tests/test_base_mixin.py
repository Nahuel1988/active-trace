"""Tests para TenantScopedMixin — TDD completo.

RED: Los tests fallan porque TenantScopedMixin no existe.
GREEN: Se implementa el mixin y los tests pasan.
TRIANGULATE: UUIDs distintos, soft delete con timestamp.

Nota técnica: cada test crea su propio engine DDL EFÍMERO con NullPool
para evitar contención de pool y problemas de event loop cross-test.
"""

import uuid
from datetime import datetime

import pytest
from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import Mapped, mapped_column

from app.core.config import Settings
from app.core.database import Base

pytestmark = pytest.mark.requires_db


class TestMixinUUIDAutoGeneration:
    """Scenario: UUID generado en Python antes de insertar."""

    async def test_uuid_generated_on_flush(
        self, db_session: AsyncSession, settings: Settings,
    ) -> None:
        """WHEN se hace flush, THEN id tiene UUID v4."""
        from app.models.base import TenantScopedMixin

        class M1(TenantScopedMixin, Base):
            __tablename__ = "_t1_id"
            name: Mapped[str] = mapped_column(nullable=False)

        url = settings.test_database_url or settings.database_url
        async with create_async_engine(url, poolclass=NullPool).begin() as conn:
            await conn.run_sync(
                Base.metadata.create_all,
                tables=[M1.__table__],
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

        obj = M1(name="test", tenant_id=tenant.id)
        db_session.add(obj)
        await db_session.flush()

        assert obj.id is not None
        assert isinstance(obj.id, uuid.UUID)


class TestMixinTimestamps:
    """Scenario: Timestamps auto-gestionados en INSERT y UPDATE."""

    async def test_created_and_updated_set_on_insert(
        self, db_session: AsyncSession, settings: Settings,
    ) -> None:
        """WHEN se persiste un modelo, THEN created_at y updated_at son datetime."""
        from app.models.base import TenantScopedMixin

        class M2(TenantScopedMixin, Base):
            __tablename__ = "_t2_ts"
            name: Mapped[str] = mapped_column(nullable=False)

        url = settings.test_database_url or settings.database_url
        async with create_async_engine(url, poolclass=NullPool).begin() as conn:
            await conn.run_sync(
                Base.metadata.create_all,
                tables=[M2.__table__],
            )

        from app.models.tenant import Tenant

        tenant = Tenant(
            id=uuid.uuid4(),
            slug=f"test-{uuid.uuid4().hex[:8]}",
            nombre="Test",
            activo=True,
        )
        db_session.add(tenant)
        await db_session.commit()

        obj = M2(name="test", tenant_id=tenant.id)
        db_session.add(obj)
        await db_session.commit()
        await db_session.refresh(obj)

        assert isinstance(obj.created_at, datetime)
        assert isinstance(obj.updated_at, datetime)


class TestMixinSoftDelete:
    """TRIANGULATE: soft delete con timestamp initial None."""

    async def test_deleted_at_starts_none(
        self, db_session: AsyncSession, settings: Settings,
    ) -> None:
        """WHEN se crea un modelo, THEN deleted_at es None."""
        from app.models.base import TenantScopedMixin

        class M3(TenantScopedMixin, Base):
            __tablename__ = "_t3_del"
            name: Mapped[str] = mapped_column(nullable=False)

        url = settings.test_database_url or settings.database_url
        async with create_async_engine(url, poolclass=NullPool).begin() as conn:
            await conn.run_sync(
                Base.metadata.create_all,
                tables=[M3.__table__],
            )

        from app.models.tenant import Tenant

        tenant = Tenant(
            id=uuid.uuid4(),
            slug=f"test-{uuid.uuid4().hex[:8]}",
            nombre="Test",
            activo=True,
        )
        db_session.add(tenant)
        await db_session.commit()

        obj = M3(name="test", tenant_id=tenant.id)
        db_session.add(obj)
        await db_session.commit()

        assert obj.deleted_at is None


class TestMixinDistinctUUIDs:
    """TRIANGULATE: Dos instancias tienen UUIDs distintos."""

    async def test_two_instances_have_different_uuids(
        self, db_session: AsyncSession, settings: Settings,
    ) -> None:
        """WHEN se crean dos instancias, THEN tienen UUIDs diferentes."""
        from app.models.base import TenantScopedMixin

        class M4(TenantScopedMixin, Base):
            __tablename__ = "_t4_dist"
            name: Mapped[str] = mapped_column(nullable=False)

        url = settings.test_database_url or settings.database_url
        async with create_async_engine(url, poolclass=NullPool).begin() as conn:
            await conn.run_sync(
                Base.metadata.create_all,
                tables=[M4.__table__],
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

        o1 = M4(name="a", tenant_id=tenant.id)
        o2 = M4(name="b", tenant_id=tenant.id)
        db_session.add_all([o1, o2])
        await db_session.flush()

        assert o1.id != o2.id


class TestMixinSoftDeleteTimestamp:
    """TRIANGULATE: soft delete setea deleted_at."""

    async def test_soft_delete_sets_deleted_at(
        self, db_session: AsyncSession, settings: Settings,
    ) -> None:
        """WHEN se setea deleted_at, THEN persiste."""
        from app.models.base import TenantScopedMixin

        class M5(TenantScopedMixin, Base):
            __tablename__ = "_t5_sd"
            name: Mapped[str] = mapped_column(nullable=False)

        url = settings.test_database_url or settings.database_url
        async with create_async_engine(url, poolclass=NullPool).begin() as conn:
            await conn.run_sync(
                Base.metadata.create_all,
                tables=[M5.__table__],
            )

        from app.models.tenant import Tenant
        from sqlalchemy import func

        tenant = Tenant(
            id=uuid.uuid4(),
            slug=f"test-{uuid.uuid4().hex[:8]}",
            nombre="Test",
            activo=True,
        )
        db_session.add(tenant)
        await db_session.commit()

        obj = M5(name="delete-me", tenant_id=tenant.id)
        db_session.add(obj)
        await db_session.commit()
        await db_session.refresh(obj)

        assert obj.deleted_at is None

        obj.deleted_at = func.now()
        await db_session.commit()
        await db_session.refresh(obj)

        assert obj.deleted_at is not None
        assert isinstance(obj.deleted_at, datetime)

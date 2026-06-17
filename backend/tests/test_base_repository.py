"""Tests para BaseRepository — TDD.

RED: Los tests fallan porque BaseRepository no existe.
GREEN: Se implementa y los tests pasan.
TRIANGULATE: Aislamiento cross-tenant, limit.
"""

import uuid

import pytest
from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import Mapped, mapped_column

from app.core.config import Settings
from app.core.database import Base

pytestmark = pytest.mark.requires_db


class TestRepositoryGet:
    """Scenario: get() con scope de tenant."""

    async def test_get_returns_none_for_other_tenant(
        self, db_session: AsyncSession, settings: Settings,
    ) -> None:
        """WHEN get(id=x, tenant_id=t1) y x pertenece a t2, THEN retorna None."""
        from app.models.base import TenantScopedMixin

        class M1(TenantScopedMixin, Base):
            __tablename__ = "_r1_get"
            name: Mapped[str] = mapped_column(nullable=False)

        url = settings.test_database_url or settings.database_url
        async with create_async_engine(url, poolclass=NullPool).begin() as conn:
            await conn.run_sync(
                Base.metadata.create_all,
                tables=[M1.__table__],
            )

        from app.models.tenant import Tenant

        t1 = Tenant(id=uuid.uuid4(), slug=f"t1-{uuid.uuid4().hex[:8]}", nombre="T1")
        t2 = Tenant(id=uuid.uuid4(), slug=f"t2-{uuid.uuid4().hex[:8]}", nombre="T2")
        db_session.add_all([t1, t2])
        await db_session.flush()

        o2 = M1(name="other-tenant", tenant_id=t2.id)
        db_session.add(o2)
        await db_session.flush()

        from app.repositories.base import BaseRepository

        repo = BaseRepository(M1)
        result = await repo.get(id=o2.id, tenant_id=t1.id, session=db_session)

        assert result is None

    async def test_get_returns_correct_tenant_record(
        self, db_session: AsyncSession, settings: Settings,
    ) -> None:
        """WHEN get(id=x, tenant_id=t1) y x pertenece a t1, THEN retorna el registro."""
        from app.models.base import TenantScopedMixin

        class M2(TenantScopedMixin, Base):
            __tablename__ = "_r1b_get"
            name: Mapped[str] = mapped_column(nullable=False)

        url = settings.test_database_url or settings.database_url
        async with create_async_engine(url, poolclass=NullPool).begin() as conn:
            await conn.run_sync(
                Base.metadata.create_all,
                tables=[M2.__table__],
            )

        from app.models.tenant import Tenant

        tenant = Tenant(
            id=uuid.uuid4(), slug=f"t-{uuid.uuid4().hex[:8]}", nombre="Test",
        )
        db_session.add(tenant)
        await db_session.flush()

        obj = M2(name="mine", tenant_id=tenant.id)
        db_session.add(obj)
        await db_session.flush()

        from app.repositories.base import BaseRepository

        repo = BaseRepository(M2)
        result = await repo.get(id=obj.id, tenant_id=tenant.id, session=db_session)

        assert result is not None
        assert result.name == "mine"


class TestRepositoryList:
    """Scenario: list() filtra por tenant."""

    async def test_list_returns_only_tenant_records(
        self, db_session: AsyncSession, settings: Settings,
    ) -> None:
        """WHEN hay registros de t1 y t2, THEN list(tenant_id=t1) solo retorna t1."""
        from app.models.base import TenantScopedMixin

        class M3(TenantScopedMixin, Base):
            __tablename__ = "_r2_list"
            name: Mapped[str] = mapped_column(nullable=False)

        url = settings.test_database_url or settings.database_url
        async with create_async_engine(url, poolclass=NullPool).begin() as conn:
            await conn.run_sync(
                Base.metadata.create_all,
                tables=[M3.__table__],
            )

        from app.models.tenant import Tenant

        t1 = Tenant(id=uuid.uuid4(), slug=f"t1-{uuid.uuid4().hex[:8]}", nombre="T1")
        t2 = Tenant(id=uuid.uuid4(), slug=f"t2-{uuid.uuid4().hex[:8]}", nombre="T2")
        db_session.add_all([t1, t2])
        await db_session.flush()

        for i in range(3):
            db_session.add(M3(name=f"t1-{i}", tenant_id=t1.id))
        for i in range(2):
            db_session.add(M3(name=f"t2-{i}", tenant_id=t2.id))
        await db_session.flush()

        from app.repositories.base import BaseRepository

        repo = BaseRepository(M3)
        results = await repo.list(tenant_id=t1.id, session=db_session)

        assert len(results) == 3
        all_t1 = all(r.tenant_id == t1.id for r in results)
        assert all_t1


class TestRepositorySoftDelete:
    """Scenario: soft_delete y comportamiento post-eliminación."""

    async def test_soft_delete_then_get_returns_none(
        self, db_session: AsyncSession, settings: Settings,
    ) -> None:
        """WHEN soft-delete, THEN get() ya no lo retorna."""
        from app.models.base import TenantScopedMixin

        class M4(TenantScopedMixin, Base):
            __tablename__ = "_r4_sd"
            name: Mapped[str] = mapped_column(nullable=False)

        url = settings.test_database_url or settings.database_url
        async with create_async_engine(url, poolclass=NullPool).begin() as conn:
            await conn.run_sync(
                Base.metadata.create_all,
                tables=[M4.__table__],
            )

        from app.models.tenant import Tenant

        tenant = Tenant(
            id=uuid.uuid4(), slug=f"t-{uuid.uuid4().hex[:8]}", nombre="Test",
        )
        db_session.add(tenant)
        await db_session.flush()

        obj = M4(name="delete-me", tenant_id=tenant.id)
        db_session.add(obj)
        await db_session.flush()

        from app.repositories.base import BaseRepository

        repo = BaseRepository(M4)
        ok = await repo.soft_delete(id=obj.id, tenant_id=tenant.id, session=db_session)
        assert ok is True

        # Liberar la sesión local antes de la next query
        await db_session.commit()

        result = await repo.get(id=obj.id, tenant_id=tenant.id, session=db_session)
        assert result is None

    async def test_soft_delete_other_tenant_does_nothing(
        self, db_session: AsyncSession, settings: Settings,
    ) -> None:
        """WHEN soft_delete(id=x, tenant_id=t1) y x pertenece a t2, THEN retorna False."""
        from app.models.base import TenantScopedMixin

        class M5(TenantScopedMixin, Base):
            __tablename__ = "_r5_ot"
            name: Mapped[str] = mapped_column(nullable=False)

        url = settings.test_database_url or settings.database_url
        async with create_async_engine(url, poolclass=NullPool).begin() as conn:
            await conn.run_sync(
                Base.metadata.create_all,
                tables=[M5.__table__],
            )

        from app.models.tenant import Tenant

        t1 = Tenant(id=uuid.uuid4(), slug=f"t1-{uuid.uuid4().hex[:8]}", nombre="T1")
        t2 = Tenant(id=uuid.uuid4(), slug=f"t2-{uuid.uuid4().hex[:8]}", nombre="T2")
        db_session.add_all([t1, t2])
        await db_session.flush()

        obj_t2 = M5(name="other", tenant_id=t2.id)
        db_session.add(obj_t2)
        await db_session.flush()

        from app.repositories.base import BaseRepository

        repo = BaseRepository(M5)
        ok = await repo.soft_delete(id=obj_t2.id, tenant_id=t1.id, session=db_session)
        assert ok is False

    async def test_soft_delete_then_list_excludes(
        self, db_session: AsyncSession, settings: Settings,
    ) -> None:
        """WHEN soft-delete, THEN list() no lo incluye."""
        from app.models.base import TenantScopedMixin

        class M6(TenantScopedMixin, Base):
            __tablename__ = "_r6_se"
            name: Mapped[str] = mapped_column(nullable=False)

        url = settings.test_database_url or settings.database_url
        async with create_async_engine(url, poolclass=NullPool).begin() as conn:
            await conn.run_sync(
                Base.metadata.create_all,
                tables=[M6.__table__],
            )

        from app.models.tenant import Tenant

        tenant = Tenant(
            id=uuid.uuid4(), slug=f"t-{uuid.uuid4().hex[:8]}", nombre="Test",
        )
        db_session.add(tenant)
        await db_session.flush()

        o1 = M6(name="keep", tenant_id=tenant.id)
        o2 = M6(name="remove", tenant_id=tenant.id)
        db_session.add_all([o1, o2])
        await db_session.flush()

        from app.repositories.base import BaseRepository

        repo = BaseRepository(M6)
        await repo.soft_delete(id=o2.id, tenant_id=tenant.id, session=db_session)
        await db_session.commit()

        results = await repo.list(tenant_id=tenant.id, session=db_session)
        names = [r.name for r in results]

        assert "remove" not in names
        assert "keep" in names


class TestRepositoryCreate:
    """Scenario: create() persiste y retorna el obj."""

    async def test_create_returns_obj_with_id(
        self, db_session: AsyncSession, settings: Settings,
    ) -> None:
        """WHEN create, THEN objeto queda en DB con id asignado."""
        from app.models.base import TenantScopedMixin

        class M7(TenantScopedMixin, Base):
            __tablename__ = "_r7_cr"
            name: Mapped[str] = mapped_column(nullable=False)

        url = settings.test_database_url or settings.database_url
        async with create_async_engine(url, poolclass=NullPool).begin() as conn:
            await conn.run_sync(
                Base.metadata.create_all,
                tables=[M7.__table__],
            )

        from app.models.tenant import Tenant

        tenant = Tenant(
            id=uuid.uuid4(), slug=f"t-{uuid.uuid4().hex[:8]}", nombre="Test",
        )
        db_session.add(tenant)
        await db_session.flush()

        from app.repositories.base import BaseRepository

        repo = BaseRepository(M7)
        obj = M7(name="created", tenant_id=tenant.id)
        result = await repo.create(obj=obj, session=db_session)

        assert result.id is not None
        assert result.name == "created"

        # Verificar que persiste en DB con una sesión nueva
        obj_id = result.id
        await db_session.commit()

        from app.core.database import create_session_factory
        factory = create_session_factory(db_session.bind)
        new_session = factory()
        try:
            fetched = await new_session.get(M7, obj_id)
            assert fetched is not None
            assert fetched.name == "created"
        finally:
            await new_session.close()


class TestRepositoryListLimit:
    """TRIANGULATE: list() con limit."""

    async def test_list_limit_max_results(
        self, db_session: AsyncSession, settings: Settings,
    ) -> None:
        """WHEN list(limit=1), THEN máximo 1 resultado."""
        from app.models.base import TenantScopedMixin

        class M8(TenantScopedMixin, Base):
            __tablename__ = "_r8_lim"
            name: Mapped[str] = mapped_column(nullable=False)

        url = settings.test_database_url or settings.database_url
        async with create_async_engine(url, poolclass=NullPool).begin() as conn:
            await conn.run_sync(
                Base.metadata.create_all,
                tables=[M8.__table__],
            )

        from app.models.tenant import Tenant

        tenant = Tenant(
            id=uuid.uuid4(), slug=f"t-{uuid.uuid4().hex[:8]}", nombre="Test",
        )
        db_session.add(tenant)
        await db_session.flush()

        for i in range(3):
            db_session.add(M8(name=f"item-{i}", tenant_id=tenant.id))
        await db_session.flush()

        from app.repositories.base import BaseRepository

        repo = BaseRepository(M8)
        results = await repo.list(tenant_id=tenant.id, session=db_session, limit=1)

        assert len(results) <= 1

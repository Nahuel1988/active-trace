"""Tests para Role y UserRole models — TDD.

RED: Tests fallan porque Role/UserRole no existen.
GREEN: Se implementan y los tests pasan.
TRIANGULATE: roles vigentes vs vencidos.
"""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import NullPool, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.config import Settings
from app.core.database import Base

pytestmark = pytest.mark.requires_db


class TestRolePersistence:
    """Scenario: Role persiste con UUID, tenant_id y code único por tenant."""

    async def test_role_has_uuid_tenant_and_timestamps(
        self,
        db_session: AsyncSession,
        settings: Settings,
    ) -> None:
        """WHEN se persiste un Role, THEN tiene UUID, tenant_id y timestamps."""
        from app.models.role import Role

        url = settings.test_database_url or settings.database_url
        async with create_async_engine(url, poolclass=NullPool).begin() as conn:
            await conn.run_sync(
                Base.metadata.create_all,
                tables=[Role.__table__],
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

        role = Role(
            tenant_id=tenant.id,
            code="admin",
            nombre="Administrador",
        )
        db_session.add(role)
        await db_session.commit()
        await db_session.refresh(role)

        assert role.id is not None
        assert isinstance(role.id, uuid.UUID)
        assert role.tenant_id == tenant.id
        assert role.code == "admin"
        assert role.nombre == "Administrador"
        assert role.created_at is not None
        assert role.updated_at is not None


class _UserRoleTestBase:
    """Mixin con factory methods para tests de UserRole."""

    @staticmethod
    async def _create_all_tables(url: str, settings: Settings) -> None:
        """Crea todas las tablas necesarias para UserRole tests."""
        from app.models.role import Role, UserRole
        from app.models.user import User

        async with create_async_engine(url, poolclass=NullPool).begin() as conn:
            await conn.run_sync(
                Base.metadata.create_all,
                tables=[
                    UserRole.__table__,
                    Role.__table__,
                    User.__table__,
                ],
            )

    @staticmethod
    async def _create_tenant_and_user(
        db_session: AsyncSession,
    ) -> tuple:
        """Crea tenant + user de prueba. Retorna (tenant, user)."""
        from app.models.tenant import Tenant
        from app.models.user import User

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

        return tenant, user


class TestUserRolePersistence(_UserRoleTestBase):
    """Scenario: UserRole es una tabla de asociación con vigencia."""

    async def test_user_role_persists_with_composite_pk(
        self,
        db_session: AsyncSession,
        settings: Settings,
    ) -> None:
        """WHEN se asigna un rol a un usuario, THEN persiste con desde."""
        from app.models.role import Role, UserRole

        url = settings.test_database_url or settings.database_url
        await self._create_all_tables(url, settings)

        tenant, user = await self._create_tenant_and_user(db_session)

        role = Role(
            tenant_id=tenant.id,
            code="profesor",
            nombre="Profesor",
        )
        db_session.add(role)
        await db_session.flush()

        ur = UserRole(
            user_id=user.id,
            role_id=role.id,
            tenant_id=tenant.id,
        )
        db_session.add(ur)
        await db_session.commit()
        await db_session.refresh(ur)

        assert ur.user_id == user.id
        assert ur.role_id == role.id
        assert ur.tenant_id == tenant.id
        assert ur.desde is not None
        assert ur.hasta is None

    async def test_user_role_default_desde_is_now(
        self,
        db_session: AsyncSession,
        settings: Settings,
    ) -> None:
        """WHEN se crea UserRole sin desde, THEN default es ahora (server_default)."""
        from app.models.role import Role, UserRole

        url = settings.test_database_url or settings.database_url
        await self._create_all_tables(url, settings)

        tenant, user = await self._create_tenant_and_user(db_session)

        role = Role(
            tenant_id=tenant.id,
            code="tutor",
            nombre="Tutor",
        )
        db_session.add(role)
        await db_session.flush()

        before = datetime.now(timezone.utc)
        ur = UserRole(
            user_id=user.id,
            role_id=role.id,
            tenant_id=tenant.id,
        )
        db_session.add(ur)
        await db_session.commit()
        await db_session.refresh(ur)
        after = datetime.now(timezone.utc)

        assert ur.desde is not None
        assert before - timedelta(seconds=5) <= ur.desde <= after + timedelta(seconds=5)


class TestUserRoleActiveVsExpired(_UserRoleTestBase):
    """TRIANGULATE: roles efectivos = unión de vigentes (no expirados)."""

    async def test_active_role_excludes_expired_assignment(
        self,
        db_session: AsyncSession,
        settings: Settings,
    ) -> None:
        """WHEN una asignación tiene hasta vencido, THEN se excluye de vigentes."""
        from app.models.role import Role, UserRole

        url = settings.test_database_url or settings.database_url
        await self._create_all_tables(url, settings)

        tenant, user = await self._create_tenant_and_user(db_session)

        role_active = Role(tenant_id=tenant.id, code="activo", nombre="Activo")
        role_expired = Role(tenant_id=tenant.id, code="vencido", nombre="Vencido")
        db_session.add_all([role_active, role_expired])
        await db_session.flush()

        # Asignación vigente (sin hasta)
        ur_active = UserRole(
            user_id=user.id,
            role_id=role_active.id,
            tenant_id=tenant.id,
        )
        db_session.add(ur_active)

        # Asignación vencida (con hasta en el pasado)
        ur_expired = UserRole(
            user_id=user.id,
            role_id=role_expired.id,
            tenant_id=tenant.id,
            hasta=datetime.now(timezone.utc) - timedelta(days=1),
        )
        db_session.add(ur_expired)
        await db_session.commit()

        # Consultar roles vigentes: hasta IS NULL OR hasta > now()
        result = await db_session.execute(
            select(UserRole).where(
                UserRole.user_id == user.id,
                UserRole.tenant_id == tenant.id,
                (UserRole.hasta.is_(None)) | (UserRole.hasta > datetime.now(timezone.utc)),
            )
        )
        active_roles = result.scalars().all()

        assert len(active_roles) == 1
        assert active_roles[0].role_id == role_active.id

    async def test_expired_assignment_persists_historically(
        self,
        db_session: AsyncSession,
        settings: Settings,
    ) -> None:
        """WHEN una asignación está vencida, THEN el registro histórico persiste."""
        from app.models.role import Role, UserRole

        url = settings.test_database_url or settings.database_url
        await self._create_all_tables(url, settings)

        tenant, user = await self._create_tenant_and_user(db_session)

        role = Role(tenant_id=tenant.id, code="hist", nombre="Histórico")
        db_session.add(role)
        await db_session.flush()

        ur = UserRole(
            user_id=user.id,
            role_id=role.id,
            tenant_id=tenant.id,
            hasta=datetime.now(timezone.utc) - timedelta(days=30),
        )
        db_session.add(ur)
        await db_session.commit()

        # El registro existe en DB aunque esté vencido
        result = await db_session.execute(
            select(UserRole).where(
                UserRole.user_id == user.id,
                UserRole.role_id == role.id,
                UserRole.tenant_id == tenant.id,
            )
        )
        persisted = result.scalar_one_or_none()

        assert persisted is not None
        assert persisted.hasta is not None
        assert persisted.hasta < datetime.now(timezone.utc)

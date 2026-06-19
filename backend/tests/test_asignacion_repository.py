"""Tests para AsignacionRepository — TDD C-07.

RED: tests fallan porque el repositorio no existe.
GREEN: se crea el repositorio y los tests pasan.
TRIANGULATE: filtro estado_vigencia, soft-delete, tenant isolation.

Require DB real (--run-db).
"""

import uuid
import pytest
from datetime import datetime, timezone, timedelta

pytestmark = pytest.mark.requires_db


async def _make_user(db_session, tenant_id):
    """Helper: crea un usuario para los tests."""
    from app.repositories.usuario_repository import UsuarioRepository

    repo = UsuarioRepository()
    return await repo.create(
        tenant_id=tenant_id,
        email=f"u-{uuid.uuid4().hex[:6]}@test.edu.ar",
        password_plain="pw",
        nombre="Test",
        apellidos="User",
        session=db_session,
    )


async def _make_role(db_session, tenant_id, code="PROFESOR"):
    """Helper: crea un rol para los tests."""
    from app.models.role import Role

    role = Role(
        tenant_id=tenant_id,
        code=f"{code}-{uuid.uuid4().hex[:4]}",
        nombre=code,
    )
    db_session.add(role)
    await db_session.flush()
    await db_session.refresh(role)
    return role


class TestAsignacionRepositoryCRUD:
    """Scenario: CRUD básico de asignaciones."""

    async def test_create_asignacion_happy_path(self, db_session, tenant_factory) -> None:
        """WHEN se crea una asignación, THEN persiste con UUID y tenant_id."""
        from app.repositories.asignacion_repository import AsignacionRepository

        tenant = await tenant_factory()
        user = await _make_user(db_session, tenant.id)
        role = await _make_role(db_session, tenant.id)
        repo = AsignacionRepository()

        asig = await repo.create(
            tenant_id=tenant.id,
            usuario_id=user.id,
            role_id=role.id,
            desde=datetime.now(timezone.utc) - timedelta(days=1),
            session=db_session,
        )

        assert asig.id is not None
        assert asig.tenant_id == tenant.id
        assert asig.usuario_id == user.id

    async def test_get_asignacion_by_id(self, db_session, tenant_factory) -> None:
        """WHEN se busca por ID, THEN retorna la asignación."""
        from app.repositories.asignacion_repository import AsignacionRepository

        tenant = await tenant_factory()
        user = await _make_user(db_session, tenant.id)
        role = await _make_role(db_session, tenant.id)
        repo = AsignacionRepository()

        asig = await repo.create(
            tenant_id=tenant.id,
            usuario_id=user.id,
            role_id=role.id,
            desde=datetime.now(timezone.utc),
            session=db_session,
        )

        found = await repo.get(id=asig.id, tenant_id=tenant.id, session=db_session)
        assert found is not None
        assert found.id == asig.id


class TestAsignacionRepositoryTenantIsolation:
    """Scenario: Tenant isolation en lectura."""

    async def test_get_other_tenant_returns_none(self, db_session, tenant_factory) -> None:
        """WHEN se busca asignación de tenant A desde tenant B, THEN None."""
        from app.repositories.asignacion_repository import AsignacionRepository

        tenant_a = await tenant_factory(slug=f"a-{uuid.uuid4().hex[:6]}")
        tenant_b = await tenant_factory(slug=f"b-{uuid.uuid4().hex[:6]}")
        user = await _make_user(db_session, tenant_a.id)
        role = await _make_role(db_session, tenant_a.id)
        repo = AsignacionRepository()

        asig = await repo.create(
            tenant_id=tenant_a.id,
            usuario_id=user.id,
            role_id=role.id,
            desde=datetime.now(timezone.utc),
            session=db_session,
        )

        # Buscar desde tenant_b no debe encontrar la asignación de tenant_a
        found = await repo.get(id=asig.id, tenant_id=tenant_b.id, session=db_session)
        assert found is None


class TestAsignacionRepositoryFiltroVigencia:
    """TRIANGULATE: filtro por estado_vigencia en query."""

    async def test_list_vigentes_excludes_vencidas(self, db_session, tenant_factory) -> None:
        """WHEN se listan con estado_vigencia=vigente, THEN solo aparecen vigentes."""
        from app.repositories.asignacion_repository import AsignacionRepository

        tenant = await tenant_factory()
        user = await _make_user(db_session, tenant.id)
        role = await _make_role(db_session, tenant.id)
        repo = AsignacionRepository()

        # Crear una vigente
        vigente = await repo.create(
            tenant_id=tenant.id,
            usuario_id=user.id,
            role_id=role.id,
            desde=datetime.now(timezone.utc) - timedelta(days=5),
            hasta=datetime.now(timezone.utc) + timedelta(days=30),
            session=db_session,
        )

        # Crear una vencida
        vencida = await repo.create(
            tenant_id=tenant.id,
            usuario_id=user.id,
            role_id=role.id,
            desde=datetime.now(timezone.utc) - timedelta(days=10),
            hasta=datetime.now(timezone.utc) - timedelta(days=1),
            session=db_session,
        )

        result_vigentes = await repo.list(
            tenant_id=tenant.id,
            estado_vigencia="vigente",
            session=db_session,
        )

        ids = {str(a.id) for a in result_vigentes}
        assert str(vigente.id) in ids
        assert str(vencida.id) not in ids

    async def test_list_todas_includes_vencidas_not_deleted(
        self, db_session, tenant_factory
    ) -> None:
        """WHEN estado_vigencia=todas, THEN incluye vencidas pero NO soft-deleted."""
        from app.repositories.asignacion_repository import AsignacionRepository

        tenant = await tenant_factory()
        user = await _make_user(db_session, tenant.id)
        role = await _make_role(db_session, tenant.id)
        repo = AsignacionRepository()

        vencida = await repo.create(
            tenant_id=tenant.id,
            usuario_id=user.id,
            role_id=role.id,
            desde=datetime.now(timezone.utc) - timedelta(days=10),
            hasta=datetime.now(timezone.utc) - timedelta(days=1),
            session=db_session,
        )

        soft_del = await repo.create(
            tenant_id=tenant.id,
            usuario_id=user.id,
            role_id=role.id,
            desde=datetime.now(timezone.utc) - timedelta(days=5),
            session=db_session,
        )
        await repo.soft_delete(id=soft_del.id, tenant_id=tenant.id, session=db_session)

        result = await repo.list(
            tenant_id=tenant.id,
            estado_vigencia="todas",
            session=db_session,
        )

        ids = {str(a.id) for a in result}
        assert str(vencida.id) in ids
        assert str(soft_del.id) not in ids


class TestAsignacionRepositorySoftDelete:
    """Scenario: soft delete excluye del listado default."""

    async def test_soft_deleted_not_in_default_list(self, db_session, tenant_factory) -> None:
        """WHEN se soft-deletea, THEN no aparece en listado sin filtros."""
        from app.repositories.asignacion_repository import AsignacionRepository

        tenant = await tenant_factory()
        user = await _make_user(db_session, tenant.id)
        role = await _make_role(db_session, tenant.id)
        repo = AsignacionRepository()

        asig = await repo.create(
            tenant_id=tenant.id,
            usuario_id=user.id,
            role_id=role.id,
            desde=datetime.now(timezone.utc),
            session=db_session,
        )

        await repo.soft_delete(id=asig.id, tenant_id=tenant.id, session=db_session)

        result = await repo.list(tenant_id=tenant.id, session=db_session)
        ids = {str(a.id) for a in result}
        assert str(asig.id) not in ids

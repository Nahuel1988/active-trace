"""Tests for FechaAcademicaRepository."""

from datetime import datetime, timezone
from uuid import UUID

import pytest

from app.models.materia import Materia
from app.models.carrera import Carrera
from app.models.cohorte import Cohorte

pytestmark = pytest.mark.requires_db


class TestFechaAcademicaRepository:
    """RED: tests for FechaAcademicaRepository."""

    async def _setup(self, db_session, tenant_factory):
        from app.models.fecha_academica import FechaAcademica, TipoFechaAcademica

        tenant = await tenant_factory(db_session)
        carrera = Carrera(tenant_id=tenant.id, codigo="C1", nombre="C Test")
        db_session.add(carrera)
        await db_session.flush()
        materia = Materia(tenant_id=tenant.id, codigo="M1", nombre="M Test")
        db_session.add(materia)
        await db_session.flush()
        cohorte = Cohorte(
            tenant_id=tenant.id, carrera_id=carrera.id,
            nombre="Coh A", anio=2026, vig_desde="2026-01-01",
        )
        db_session.add(cohorte)
        await db_session.flush()
        return tenant, carrera, materia, cohorte, FechaAcademica, TipoFechaAcademica

    async def test_create_and_get_by_id(self, db_session, create_test_schema, tenant_factory):
        from app.repositories.fecha_academica_repository import FechaAcademicaRepository

        tenant, _, materia, cohorte, FA, TFA = await self._setup(db_session, tenant_factory)
        repo = FechaAcademicaRepository()

        obj = FA(
            tenant_id=tenant.id, materia_id=materia.id, cohorte_id=cohorte.id,
            tipo=TFA.Parcial, numero=1, periodo="2026-1",
            fecha=datetime(2026, 4, 15, 10, 0, 0, tzinfo=timezone.utc),
            titulo="Parcial 1",
        )
        created = await repo.create(obj=obj, session=db_session)
        assert created.id is not None

        found = await repo.get(id=created.id, tenant_id=tenant.id, session=db_session)
        assert found is not None
        assert found.titulo == "Parcial 1"

    async def test_get_by_id_other_tenant_returns_none(self, db_session, create_test_schema, tenant_factory):
        from app.repositories.fecha_academica_repository import FechaAcademicaRepository

        tenant, _, materia, cohorte, FA, TFA = await self._setup(db_session, tenant_factory)
        repo = FechaAcademicaRepository()

        obj = FA(
            tenant_id=tenant.id, materia_id=materia.id, cohorte_id=cohorte.id,
            tipo=TFA.Parcial, numero=1, periodo="2026-1",
            fecha=datetime(2026, 4, 15, 10, 0, 0, tzinfo=timezone.utc),
            titulo="Parcial 1",
        )
        created = await repo.create(obj=obj, session=db_session)

        found = await repo.get(id=created.id, tenant_id=UUID("00000000-0000-0000-0000-000000000000"), session=db_session)
        assert found is None

    async def test_list_ordered_by_fecha(self, db_session, create_test_schema, tenant_factory):
        from app.repositories.fecha_academica_repository import FechaAcademicaRepository

        tenant, _, materia, cohorte, FA, TFA = await self._setup(db_session, tenant_factory)
        repo = FechaAcademicaRepository()

        f1 = FA(
            tenant_id=tenant.id, materia_id=materia.id, cohorte_id=cohorte.id,
            tipo=TFA.Parcial, numero=1, periodo="2026-1",
            fecha=datetime(2026, 5, 15, 10, 0, 0, tzinfo=timezone.utc),
            titulo="Parcial 1",
        )
        f2 = FA(
            tenant_id=tenant.id, materia_id=materia.id, cohorte_id=cohorte.id,
            tipo=TFA.Parcial, numero=2, periodo="2026-1",
            fecha=datetime(2026, 4, 15, 10, 0, 0, tzinfo=timezone.utc),
            titulo="Parcial 2",
        )
        db_session.add_all([f1, f2])
        await db_session.flush()

        results = await repo.list(tenant_id=tenant.id, session=db_session)
        assert len(results) == 2
        assert results[0].titulo == "Parcial 2"  # earlier date first
        assert results[1].titulo == "Parcial 1"

    async def test_list_with_filters(self, db_session, create_test_schema, tenant_factory):
        from app.repositories.fecha_academica_repository import FechaAcademicaRepository

        tenant, _, materia, cohorte, FA, TFA = await self._setup(db_session, tenant_factory)
        repo = FechaAcademicaRepository()

        f1 = FA(tenant_id=tenant.id, materia_id=materia.id, cohorte_id=cohorte.id, tipo=TFA.Parcial, numero=1, periodo="2026-1", fecha=datetime(2026, 4, 15, 10, 0, 0, tzinfo=timezone.utc), titulo="P1")
        f2 = FA(tenant_id=tenant.id, materia_id=materia.id, cohorte_id=cohorte.id, tipo=TFA.TP, numero=1, periodo="2026-1", fecha=datetime(2026, 5, 15, 10, 0, 0, tzinfo=timezone.utc), titulo="TP1")
        db_session.add_all([f1, f2])
        await db_session.flush()

        results = await repo.list(tenant_id=tenant.id, session=db_session, tipo="Parcial")
        assert len(results) == 1
        assert results[0].titulo == "P1"

    async def test_get_by_instance(self, db_session, create_test_schema, tenant_factory):
        from app.repositories.fecha_academica_repository import FechaAcademicaRepository

        tenant, _, materia, cohorte, FA, TFA = await self._setup(db_session, tenant_factory)
        repo = FechaAcademicaRepository()

        obj = FA(
            tenant_id=tenant.id, materia_id=materia.id, cohorte_id=cohorte.id,
            tipo=TFA.Parcial, numero=1, periodo="2026-1",
            fecha=datetime(2026, 4, 15, 10, 0, 0, tzinfo=timezone.utc),
            titulo="P1",
        )
        await repo.create(obj=obj, session=db_session)

        found = await repo.get_by_instance(
            tenant_id=tenant.id, materia_id=materia.id,
            cohorte_id=cohorte.id, tipo=TFA.Parcial, numero=1,
            session=db_session,
        )
        assert found is not None
        assert found.titulo == "P1"

    async def test_soft_delete_excludes(self, db_session, create_test_schema, tenant_factory):
        from app.repositories.fecha_academica_repository import FechaAcademicaRepository

        tenant, _, materia, cohorte, FA, TFA = await self._setup(db_session, tenant_factory)
        repo = FechaAcademicaRepository()

        obj = FA(
            tenant_id=tenant.id, materia_id=materia.id, cohorte_id=cohorte.id,
            tipo=TFA.Parcial, numero=1, periodo="2026-1",
            fecha=datetime(2026, 4, 15, 10, 0, 0, tzinfo=timezone.utc),
            titulo="P1",
        )
        created = await repo.create(obj=obj, session=db_session)
        await repo.soft_delete(id=created.id, tenant_id=tenant.id, session=db_session)

        found = await repo.get(id=created.id, tenant_id=tenant.id, session=db_session)
        assert found is None

    async def test_tenant_isolation_in_list(self, db_session, create_test_schema, tenant_factory):
        from app.repositories.fecha_academica_repository import FechaAcademicaRepository

        tenant, _, materia, cohorte, FA, TFA = await self._setup(db_session, tenant_factory)
        repo = FechaAcademicaRepository()

        obj = FA(tenant_id=tenant.id, materia_id=materia.id, cohorte_id=cohorte.id, tipo=TFA.Parcial, numero=1, periodo="2026-1", fecha=datetime(2026, 4, 15, 10, 0, 0, tzinfo=timezone.utc), titulo="P1")
        await repo.create(obj=obj, session=db_session)

        results = await repo.list(tenant_id=UUID("00000000-0000-0000-0000-000000000000"), session=db_session)
        assert len(results) == 0

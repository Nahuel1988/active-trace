"""Tests for ProgramaMateriaRepository."""

import uuid

import pytest

from app.models.materia import Materia
from app.models.carrera import Carrera
from app.models.cohorte import Cohorte

pytestmark = pytest.mark.requires_db


class TestProgramaMateriaRepository:
    """RED: tests for ProgramaMateriaRepository."""

    async def _setup(self, db_session, tenant_factory):
        from app.models.programa_materia import ProgramaMateria

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
        return tenant, carrera, materia, cohorte, ProgramaMateria

    async def test_create_and_get_by_id(self, db_session, create_test_schema, tenant_factory):
        from app.repositories.programa_materia_repository import ProgramaMateriaRepository

        tenant, carrera, materia, cohorte, PM = await self._setup(db_session, tenant_factory)
        repo = ProgramaMateriaRepository()

        obj = PM(
            tenant_id=tenant.id, materia_id=materia.id,
            carrera_id=carrera.id, cohorte_id=cohorte.id,
            titulo="Prog 1",
        )
        created = await repo.create(obj=obj, session=db_session)
        assert created.id is not None

        found = await repo.get(id=created.id, tenant_id=tenant.id, session=db_session)
        assert found is not None
        assert found.titulo == "Prog 1"

    async def test_get_by_id_other_tenant_returns_none(self, db_session, create_test_schema, tenant_factory):
        from app.repositories.programa_materia_repository import ProgramaMateriaRepository

        tenant1, carrera, materia, cohorte, PM = await self._setup(db_session, tenant_factory)
        repo = ProgramaMateriaRepository()

        obj = PM(
            tenant_id=tenant1.id, materia_id=materia.id,
            carrera_id=carrera.id, cohorte_id=cohorte.id,
            titulo="Prog 1",
        )
        created = await repo.create(obj=obj, session=db_session)

        other_tenant_id = uuid.uuid4()
        found = await repo.get(id=created.id, tenant_id=other_tenant_id, session=db_session)
        assert found is None

    async def test_list_with_filters(self, db_session, create_test_schema, tenant_factory):
        from app.repositories.programa_materia_repository import ProgramaMateriaRepository

        tenant, carrera, materia, cohorte, PM = await self._setup(db_session, tenant_factory)
        repo = ProgramaMateriaRepository()

        # Create a second materia and cohorte for filtering
        materia2 = Materia(tenant_id=tenant.id, codigo="M2", nombre="Mat 2")
        db_session.add(materia2)
        await db_session.flush()

        pm1 = PM(tenant_id=tenant.id, materia_id=materia.id, carrera_id=carrera.id, cohorte_id=cohorte.id, titulo="P1")
        pm2 = PM(tenant_id=tenant.id, materia_id=materia2.id, carrera_id=carrera.id, cohorte_id=cohorte.id, titulo="P2")
        db_session.add(pm1)
        db_session.add(pm2)
        await db_session.flush()

        # Filter by materia_id
        results = await repo.list(tenant_id=tenant.id, session=db_session, materia_id=materia.id)
        assert len(results) == 1
        assert results[0].titulo == "P1"

    async def test_get_by_combination(self, db_session, create_test_schema, tenant_factory):
        from app.repositories.programa_materia_repository import ProgramaMateriaRepository

        tenant, carrera, materia, cohorte, PM = await self._setup(db_session, tenant_factory)
        repo = ProgramaMateriaRepository()

        obj = PM(
            tenant_id=tenant.id, materia_id=materia.id,
            carrera_id=carrera.id, cohorte_id=cohorte.id,
            titulo="Prog 1",
        )
        await repo.create(obj=obj, session=db_session)

        found = await repo.get_by_combination(
            tenant_id=tenant.id, materia_id=materia.id,
            carrera_id=carrera.id, cohorte_id=cohorte.id,
            session=db_session,
        )
        assert found is not None
        assert found.titulo == "Prog 1"

    async def test_soft_delete_excludes_from_list(self, db_session, create_test_schema, tenant_factory):
        from app.repositories.programa_materia_repository import ProgramaMateriaRepository

        tenant, carrera, materia, cohorte, PM = await self._setup(db_session, tenant_factory)
        repo = ProgramaMateriaRepository()

        obj = PM(
            tenant_id=tenant.id, materia_id=materia.id,
            carrera_id=carrera.id, cohorte_id=cohorte.id,
            titulo="Prog 1",
        )
        created = await repo.create(obj=obj, session=db_session)

        deleted = await repo.soft_delete(id=created.id, tenant_id=tenant.id, session=db_session)
        assert deleted is True

        found = await repo.get(id=created.id, tenant_id=tenant.id, session=db_session)
        assert found is None

    async def test_tenant_isolation_in_list(self, db_session, create_test_schema, tenant_factory):
        from app.repositories.programa_materia_repository import ProgramaMateriaRepository

        tenant1, carrera, materia, cohorte, PM = await self._setup(db_session, tenant_factory)
        repo = ProgramaMateriaRepository()

        pm1 = PM(tenant_id=tenant1.id, materia_id=materia.id, carrera_id=carrera.id, cohorte_id=cohorte.id, titulo="P1")
        await repo.create(obj=pm1, session=db_session)

        # List for a different tenant
        other_tenant_id = uuid.uuid4()
        results = await repo.list(tenant_id=other_tenant_id, session=db_session)
        assert len(results) == 0

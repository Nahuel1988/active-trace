import uuid

import pytest

pytestmark = pytest.mark.requires_db


class TestCarreraRepository:
    async def test_get_by_codigo_and_list_all(self, db_session, create_test_schema):
        from app.models.tenant import Tenant
        from app.models.carrera import Carrera
        from app.repositories.carrera_repository import CarreraRepository

        tenant = Tenant(id=uuid.uuid4(), slug=f"t-{uuid.uuid4().hex[:8]}", nombre="T")
        db_session.add(tenant)
        await db_session.flush()

        c = Carrera(tenant_id=tenant.id, codigo="C01", nombre="C 1")
        db_session.add(c)
        await db_session.flush()

        repo = CarreraRepository()
        found = await repo.get_by_codigo(tenant_id=tenant.id, codigo="C01", session=db_session)
        assert found is not None
        all_list = await repo.list_all(tenant_id=tenant.id, session=db_session)
        assert any(x.id == c.id for x in all_list)


class TestCohorteRepository:
    async def test_get_by_nombre_and_list_all(self, db_session, create_test_schema):
        from app.models.tenant import Tenant
        from app.models.carrera import Carrera
        from app.models.cohorte import Cohorte
        from app.repositories.cohorte_repository import CohorteRepository

        tenant = Tenant(id=uuid.uuid4(), slug=f"t-{uuid.uuid4().hex[:8]}", nombre="T")
        db_session.add(tenant)
        await db_session.flush()

        carrera = Carrera(tenant_id=tenant.id, codigo="C1", nombre="Carrera")
        db_session.add(carrera)
        await db_session.flush()

        coh = Cohorte(tenant_id=tenant.id, carrera_id=carrera.id, nombre="A", anio=2026, vig_desde="2026-01-01")
        db_session.add(coh)
        await db_session.flush()

        repo = CohorteRepository()
        found = await repo.get_by_nombre(tenant_id=tenant.id, carrera_id=carrera.id, nombre="A", session=db_session)
        assert found is not None
        all_list = await repo.list_all(tenant_id=tenant.id, session=db_session)
        assert any(x.id == coh.id for x in all_list)


class TestMateriaRepository:
    async def test_get_by_codigo_and_list_all(self, db_session, create_test_schema):
        from app.models.tenant import Tenant
        from app.models.materia import Materia
        from app.repositories.materia_repository import MateriaRepository

        tenant = Tenant(id=uuid.uuid4(), slug=f"t-{uuid.uuid4().hex[:8]}", nombre="T")
        db_session.add(tenant)
        await db_session.flush()

        m = Materia(tenant_id=tenant.id, codigo="M1", nombre="Mat")
        db_session.add(m)
        await db_session.flush()

        repo = MateriaRepository()
        found = await repo.get_by_codigo(tenant_id=tenant.id, codigo="M1", session=db_session)
        assert found is not None
        all_list = await repo.list_all(tenant_id=tenant.id, session=db_session)
        assert any(x.id == m.id for x in all_list)

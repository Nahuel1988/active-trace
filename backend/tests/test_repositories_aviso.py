import uuid
from datetime import datetime, timezone, timedelta

import pytest

pytestmark = pytest.mark.requires_db


class TestAvisoRepository:
    async def _seed_tenant(self, db_session):
        from app.models.tenant import Tenant
        t = Tenant(id=uuid.uuid4(), slug=f"t-{uuid.uuid4().hex[:8]}", nombre="T")
        db_session.add(t)
        await db_session.flush()
        return t

    async def _seed_aviso(self, db_session, tenant, **kwargs):
        from app.models.aviso import Aviso, AlcanceAviso, SeveridadAviso
        now = datetime.now(timezone.utc)
        aviso = Aviso(
            tenant_id=tenant.id,
            titulo=kwargs.get("titulo", "Test"),
            cuerpo=kwargs.get("cuerpo", "Cuerpo"),
            alcance=kwargs.get("alcance", AlcanceAviso.Global),
            severidad=kwargs.get("severidad", SeveridadAviso.Info),
            inicio_en=kwargs.get("inicio_en", now - timedelta(days=1)),
            fin_en=kwargs.get("fin_en", now + timedelta(days=1)),
            activo=kwargs.get("activo", True),
        )
        db_session.add(aviso)
        await db_session.flush()
        return aviso

    async def test_list_tenant_scoped(self, db_session):
        from app.repositories.aviso_repository import AvisoRepository

        t1 = await self._seed_tenant(db_session)
        t2 = await self._seed_tenant(db_session)
        await self._seed_aviso(db_session, t1)
        await self._seed_aviso(db_session, t2)

        repo = AvisoRepository()
        t1_avisos = await repo.list_all(tenant_id=t1.id, session=db_session)
        t2_avisos = await repo.list_all(tenant_id=t2.id, session=db_session)

        assert len(t1_avisos) == 1
        assert len(t2_avisos) == 1

    async def test_list_visibles_only_global(self, db_session):
        from app.repositories.aviso_repository import AvisoRepository

        tenant = await self._seed_tenant(db_session)
        await self._seed_aviso(db_session, tenant)

        repo = AvisoRepository()
        visibles = await repo.list_visibles(
            tenant_id=tenant.id,
            materia_ids=[],
            cohorte_ids=[],
            roles=[],
            usuario_id=uuid.uuid4(),
            session=db_session,
        )
        assert len(visibles) == 1

    async def test_list_visibles_filters_by_vigencia(self, db_session):
        from app.repositories.aviso_repository import AvisoRepository

        tenant = await self._seed_tenant(db_session)
        now = datetime.now(timezone.utc)
        await self._seed_aviso(db_session, tenant, inicio_en=now + timedelta(days=10), fin_en=now + timedelta(days=20))

        repo = AvisoRepository()
        visibles = await repo.list_visibles(
            tenant_id=tenant.id,
            materia_ids=[],
            cohorte_ids=[],
            roles=[],
            usuario_id=uuid.uuid4(),
            session=db_session,
        )
        assert len(visibles) == 0

    async def test_list_visibles_inactive_not_shown(self, db_session):
        from app.repositories.aviso_repository import AvisoRepository

        tenant = await self._seed_tenant(db_session)
        await self._seed_aviso(db_session, tenant, activo=False)

        repo = AvisoRepository()
        visibles = await repo.list_visibles(
            tenant_id=tenant.id,
            materia_ids=[],
            cohorte_ids=[],
            roles=[],
            usuario_id=uuid.uuid4(),
            session=db_session,
        )
        assert len(visibles) == 0

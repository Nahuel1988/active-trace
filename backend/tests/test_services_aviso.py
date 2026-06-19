import uuid
from datetime import datetime, timezone, timedelta

import pytest

pytestmark = pytest.mark.requires_db


class TestAvisoService:
    async def _seed_tenant(self, db_session):
        from app.models.tenant import Tenant
        t = Tenant(id=uuid.uuid4(), slug=f"t-{uuid.uuid4().hex[:8]}", nombre="T")
        db_session.add(t)
        await db_session.flush()
        return t

    async def test_create_aviso(self, db_session):
        from app.services.aviso_service import AvisoService

        tenant = await self._seed_tenant(db_session)
        svc = AvisoService()

        now = datetime.now(timezone.utc)
        a = await svc.create(tenant_id=tenant.id, data={
            "titulo": "Nuevo",
            "cuerpo": "Contenido",
            "alcance": "global",
            "severidad": "info",
            "inicio_en": now,
            "fin_en": now + timedelta(days=1),
        }, session=db_session)
        assert a.titulo == "Nuevo"
        assert a.activo is True

    async def test_create_por_materia_without_materia_id(self, db_session):
        from app.services.aviso_service import AvisoService, ServiceError

        tenant = await self._seed_tenant(db_session)
        svc = AvisoService()

        now = datetime.now(timezone.utc)
        with pytest.raises(ServiceError) as exc:
            await svc.create(tenant_id=tenant.id, data={
                "titulo": "Test",
                "cuerpo": "Cuerpo",
                "alcance": "por_materia",
                "severidad": "info",
                "inicio_en": now,
                "fin_en": now + timedelta(days=1),
            }, session=db_session)
        assert exc.value.status_code == 422

    async def test_update_aviso(self, db_session):
        from app.services.aviso_service import AvisoService

        tenant = await self._seed_tenant(db_session)
        svc = AvisoService()

        now = datetime.now(timezone.utc)
        a = await svc.create(tenant_id=tenant.id, data={
            "titulo": "Original",
            "cuerpo": "Cuerpo",
            "alcance": "global",
            "severidad": "info",
            "inicio_en": now,
            "fin_en": now + timedelta(days=1),
        }, session=db_session)

        updated = await svc.update(tenant_id=tenant.id, id=a.id, data={"titulo": "Modificado"}, session=db_session)
        assert updated.titulo == "Modificado"

    async def test_delete_aviso(self, db_session):
        from app.services.aviso_service import AvisoService

        tenant = await self._seed_tenant(db_session)
        svc = AvisoService()

        now = datetime.now(timezone.utc)
        a = await svc.create(tenant_id=tenant.id, data={
            "titulo": "Borrar",
            "cuerpo": "Cuerpo",
            "alcance": "global",
            "severidad": "info",
            "inicio_en": now,
            "fin_en": now + timedelta(days=1),
        }, session=db_session)

        deleted = await svc.delete(tenant_id=tenant.id, id=a.id, session=db_session)
        assert deleted is True

        from app.repositories.aviso_repository import AvisoRepository
        repo = AvisoRepository()
        obj = await repo.get(id=a.id, tenant_id=tenant.id, session=db_session)
        assert obj is None

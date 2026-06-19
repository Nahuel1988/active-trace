import uuid

import pytest

pytestmark = pytest.mark.requires_db


class TestMateriaService:
    async def test_create_and_duplicate(self, db_session, create_test_schema):
        from app.models.tenant import Tenant
        from app.services.materia_service import MateriaService, MateriaError

        tenant = Tenant(id=uuid.uuid4(), slug=f"t-{uuid.uuid4().hex[:8]}", nombre="T")
        db_session.add(tenant)
        await db_session.flush()

        svc = MateriaService()
        saved = await svc.create(tenant_id=tenant.id, data={"codigo": "M1", "nombre": "Mat"}, session=db_session)
        assert saved.codigo == "M1"

        with pytest.raises(MateriaError):
            await svc.create(tenant_id=tenant.id, data={"codigo": "M1", "nombre": "Mat2"}, session=db_session)

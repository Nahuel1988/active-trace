import uuid

import pytest

pytestmark = pytest.mark.requires_db


class TestCarreraService:
    async def test_create_and_duplicate(self, db_session, create_test_schema):
        from app.models.tenant import Tenant
        from app.services.carrera_service import CarreraService, ServiceError

        tenant = Tenant(id=uuid.uuid4(), slug=f"t-{uuid.uuid4().hex[:8]}", nombre="T")
        db_session.add(tenant)
        await db_session.flush()

        svc = CarreraService()
        saved = await svc.create(tenant_id=tenant.id, data={"codigo": "C1", "nombre": "C"}, session=db_session)
        assert saved.codigo == "C1"

        with pytest.raises(ServiceError):
            await svc.create(tenant_id=tenant.id, data={"codigo": "C1", "nombre": "X"}, session=db_session)

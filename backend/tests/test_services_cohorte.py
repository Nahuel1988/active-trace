import uuid

import pytest

pytestmark = pytest.mark.requires_db


class TestCohorteService:
    async def test_create_cohorte_ok_and_carrera_inactiva(self, db_session, create_test_schema):
        from app.models.tenant import Tenant
        from app.models.carrera import Carrera
        from app.services.cohorte_service import CohorteService, CohorteError

        tenant = Tenant(id=uuid.uuid4(), slug=f"t-{uuid.uuid4().hex[:8]}", nombre="T")
        db_session.add(tenant)
        await db_session.flush()

        carrera = Carrera(tenant_id=tenant.id, codigo="C1", nombre="C", estado="activa")
        db_session.add(carrera)
        await db_session.flush()

        svc = CohorteService()
        saved = await svc.create(tenant_id=tenant.id, data={"carrera_id": carrera.id, "nombre": "A", "anio": 2026, "vig_desde": "2026-01-01"}, session=db_session)
        assert saved.nombre == "A"

        # Inactivate carrera and expect create to fail
        carrera.estado = "inactiva"
        await db_session.flush()
        with pytest.raises(CohorteError):
            await svc.create(tenant_id=tenant.id, data={"carrera_id": carrera.id, "nombre": "B", "anio": 2026, "vig_desde": "2026-01-01"}, session=db_session)

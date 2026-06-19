import uuid
from datetime import datetime, timezone

import pytest

pytestmark = pytest.mark.requires_db


class TestAvisoModel:
    async def test_create_aviso(self, db_session, create_test_schema):
        from app.models.tenant import Tenant
        from app.models.aviso import Aviso, AlcanceAviso, SeveridadAviso

        tenant = Tenant(id=uuid.uuid4(), slug=f"t-{uuid.uuid4().hex[:8]}", nombre="T")
        db_session.add(tenant)
        await db_session.flush()

        now = datetime.now(timezone.utc)
        aviso = Aviso(
            tenant_id=tenant.id,
            titulo="Test Aviso",
            cuerpo="Contenido del aviso",
            alcance=AlcanceAviso.Global,
            severidad=SeveridadAviso.Info,
            inicio_en=now,
            fin_en=now,
        )
        db_session.add(aviso)
        await db_session.flush()
        await db_session.refresh(aviso)

        assert aviso.id is not None
        assert aviso.titulo == "Test Aviso"
        assert aviso.activo is True
        assert aviso.requiere_ack is False
        assert aviso.orden == 0

    async def test_aviso_with_materia(self, db_session, create_test_schema):
        from app.models.tenant import Tenant
        from app.models.aviso import Aviso, AlcanceAviso, SeveridadAviso
        from app.models.materia import Materia

        tenant = Tenant(id=uuid.uuid4(), slug=f"t-{uuid.uuid4().hex[:8]}", nombre="T")
        db_session.add(tenant)
        await db_session.flush()

        materia = Materia(tenant_id=tenant.id, codigo="M1", nombre="Mat1")
        db_session.add(materia)
        await db_session.flush()

        now = datetime.now(timezone.utc)
        aviso = Aviso(
            tenant_id=tenant.id,
            titulo="Aviso por materia",
            cuerpo="Contenido",
            alcance=AlcanceAviso.PorMateria,
            severidad=SeveridadAviso.Advertencia,
            materia_id=materia.id,
            inicio_en=now,
            fin_en=now,
        )
        db_session.add(aviso)
        await db_session.flush()

        assert aviso.materia_id == materia.id
        assert aviso.alcance == AlcanceAviso.PorMateria

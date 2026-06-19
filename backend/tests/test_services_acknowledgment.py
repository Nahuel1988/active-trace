import uuid
from datetime import datetime, timezone, timedelta

import pytest

pytestmark = pytest.mark.requires_db


class TestAcknowledgmentService:
    async def _seed_basics(self, db_session):
        from app.models.tenant import Tenant
        from app.models.aviso import Aviso, AlcanceAviso, SeveridadAviso
        from app.models.user import User

        tenant = Tenant(id=uuid.uuid4(), slug=f"t-{uuid.uuid4().hex[:8]}", nombre="T")
        db_session.add(tenant)
        await db_session.flush()

        now = datetime.now(timezone.utc)
        aviso = Aviso(
            tenant_id=tenant.id,
            titulo="Test",
            cuerpo="Cuerpo",
            alcance=AlcanceAviso.Global,
            severidad=SeveridadAviso.Info,
            inicio_en=now - timedelta(days=1),
            fin_en=now + timedelta(days=1),
            activo=True,
        )
        db_session.add(aviso)
        await db_session.flush()

        user = User(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            email_encrypted="enc",
            email_lookup="lookup",
            password_hash="hash",
            is_active=True,
        )
        db_session.add(user)
        await db_session.flush()

        return tenant, aviso, user

    async def test_confirmar_ok(self, db_session):
        from app.services.acknowledgment_service import AcknowledgmentService

        tenant, aviso, user = await self._seed_basics(db_session)
        svc = AcknowledgmentService()

        ack = await svc.confirmar(
            tenant_id=tenant.id,
            aviso_id=aviso.id,
            usuario_id=user.id,
            session=db_session,
        )
        assert ack.aviso_id == aviso.id
        assert ack.usuario_id == user.id

    async def test_confirmar_duplicado(self, db_session):
        from app.services.acknowledgment_service import AcknowledgmentService

        tenant, aviso, user = await self._seed_basics(db_session)
        svc = AcknowledgmentService()

        ack1 = await svc.confirmar(
            tenant_id=tenant.id,
            aviso_id=aviso.id,
            usuario_id=user.id,
            session=db_session,
        )
        ack2 = await svc.confirmar(
            tenant_id=tenant.id,
            aviso_id=aviso.id,
            usuario_id=user.id,
            session=db_session,
        )
        assert ack1.id == ack2.id

    async def test_confirmar_aviso_inexistente(self, db_session):
        from app.services.acknowledgment_service import AcknowledgmentService
        from app.services.aviso_service import ServiceError

        tenant, _, user = await self._seed_basics(db_session)
        svc = AcknowledgmentService()

        with pytest.raises(ServiceError) as exc:
            await svc.confirmar(
                tenant_id=tenant.id,
                aviso_id=uuid.uuid4(),
                usuario_id=user.id,
                session=db_session,
            )
        assert exc.value.status_code == 404

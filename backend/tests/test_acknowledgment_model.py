import uuid
from datetime import datetime, timezone

import pytest

pytestmark = pytest.mark.requires_db


class TestAcknowledgmentModel:
    async def test_create_ack(self, db_session, create_test_schema):
        from app.models.tenant import Tenant
        from app.models.aviso import Aviso, AlcanceAviso, SeveridadAviso
        from app.models.user import User
        from app.models.acknowledgment import AcknowledgmentAviso

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
            inicio_en=now,
            fin_en=now,
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

        ack = AcknowledgmentAviso(
            tenant_id=tenant.id,
            aviso_id=aviso.id,
            usuario_id=user.id,
        )
        db_session.add(ack)
        await db_session.flush()
        await db_session.refresh(ack)

        assert ack.id is not None
        assert ack.confirmado_at is not None

    async def test_unique_constraint(self, db_session, create_test_schema):
        from app.models.tenant import Tenant
        from app.models.aviso import Aviso, AlcanceAviso, SeveridadAviso
        from app.models.user import User
        from app.models.acknowledgment import AcknowledgmentAviso
        from sqlalchemy.exc import IntegrityError

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
            inicio_en=now,
            fin_en=now,
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

        ack1 = AcknowledgmentAviso(
            tenant_id=tenant.id,
            aviso_id=aviso.id,
            usuario_id=user.id,
        )
        db_session.add(ack1)
        await db_session.flush()

        ack2 = AcknowledgmentAviso(
            tenant_id=tenant.id,
            aviso_id=aviso.id,
            usuario_id=user.id,
        )
        db_session.add(ack2)
        with pytest.raises(IntegrityError):
            await db_session.flush()

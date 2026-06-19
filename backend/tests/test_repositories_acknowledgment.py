import uuid
from datetime import datetime, timezone

import pytest

pytestmark = pytest.mark.requires_db


class TestAcknowledgmentRepository:
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

        return tenant, aviso, user

    async def test_add_or_ignore_creates(self, db_session):
        from app.repositories.acknowledgment_repository import AcknowledgmentRepository

        tenant, aviso, user = await self._seed_basics(db_session)
        repo = AcknowledgmentRepository()

        ack = await repo.add_or_ignore(
            tenant_id=tenant.id,
            aviso_id=aviso.id,
            usuario_id=user.id,
            session=db_session,
        )
        assert ack is not None
        assert ack.aviso_id == aviso.id

    async def test_add_or_ignore_idempotent(self, db_session):
        from app.repositories.acknowledgment_repository import AcknowledgmentRepository

        tenant, aviso, user = await self._seed_basics(db_session)
        repo = AcknowledgmentRepository()

        ack1 = await repo.add_or_ignore(
            tenant_id=tenant.id,
            aviso_id=aviso.id,
            usuario_id=user.id,
            session=db_session,
        )
        ack2 = await repo.add_or_ignore(
            tenant_id=tenant.id,
            aviso_id=aviso.id,
            usuario_id=user.id,
            session=db_session,
        )
        assert ack1.id == ack2.id

    async def test_count_by_aviso(self, db_session):
        from app.repositories.acknowledgment_repository import AcknowledgmentRepository
        from app.models.user import User

        tenant, aviso, user = await self._seed_basics(db_session)
        repo = AcknowledgmentRepository()

        user2 = User(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            email_encrypted="enc2",
            email_lookup="lookup2",
            password_hash="hash",
            is_active=True,
        )
        db_session.add(user2)
        await db_session.flush()

        await repo.add_or_ignore(tenant_id=tenant.id, aviso_id=aviso.id, usuario_id=user.id, session=db_session)
        await repo.add_or_ignore(tenant_id=tenant.id, aviso_id=aviso.id, usuario_id=user2.id, session=db_session)

        count = await repo.count_by_aviso(aviso_id=aviso.id, session=db_session)
        assert count == 2

import uuid

import pytest

from app.models.padron import EntradaPadron, VersionPadron
from app.repositories.padron_repository import (
    EntradaPadronRepository,
    VersionPadronRepository,
)

pytestmark = pytest.mark.requires_db


class TestVersionPadronRepository:
    async def test_activar_version_creates_and_desactiva_previous(self, db_session, cohorte):
        t, m, c = cohorte
        repo = VersionPadronRepository()

        v1 = await repo.activar_version(
            tenant_id=t.id,
            materia_id=m.id,
            cohorte_id=c.id,
            origen="archivo",
            total_entradas=5,
            session=db_session,
        )
        assert v1.activa is True
        assert v1.origen == "archivo"

        v2 = await repo.activar_version(
            tenant_id=t.id,
            materia_id=m.id,
            cohorte_id=c.id,
            origen="moodle",
            total_entradas=3,
            session=db_session,
        )
        assert v2.activa is True
        assert v2.origen == "moodle"

        await db_session.refresh(v1)
        assert v1.activa is False

    async def test_get_version_activa_returns_correct(self, db_session, cohorte):
        t, m, c = cohorte
        repo = VersionPadronRepository()

        v = await repo.activar_version(
            tenant_id=t.id,
            materia_id=m.id,
            cohorte_id=c.id,
            origen="archivo",
            total_entradas=0,
            session=db_session,
        )

        found = await repo.get_version_activa(
            tenant_id=t.id,
            materia_id=m.id,
            cohorte_id=c.id,
            session=db_session,
        )
        assert found is not None
        assert found.id == v.id

    async def test_get_version_activa_none(self, db_session, cohorte):
        t, m, c = cohorte
        repo = VersionPadronRepository()

        found = await repo.get_version_activa(
            tenant_id=t.id,
            materia_id=m.id,
            cohorte_id=c.id,
            session=db_session,
        )
        assert found is None

    async def test_get_version_activa_excludes_other_tenant(self, db_session, tenant_factory, cohorte):
        t, m, c = cohorte
        other_t = await tenant_factory(db_session, slug="other")
        repo = VersionPadronRepository()

        await repo.activar_version(
            tenant_id=t.id,
            materia_id=m.id,
            cohorte_id=c.id,
            origen="archivo",
            total_entradas=0,
            session=db_session,
        )

        found = await repo.get_version_activa(
            tenant_id=other_t.id,
            materia_id=m.id,
            cohorte_id=c.id,
            session=db_session,
        )
        assert found is None

    async def test_soft_delete_version_works(self, db_session, cohorte):
        t, m, c = cohorte
        repo = VersionPadronRepository()

        v = await repo.activar_version(
            tenant_id=t.id,
            materia_id=m.id,
            cohorte_id=c.id,
            origen="archivo",
            total_entradas=0,
            session=db_session,
        )

        ok = await repo.soft_delete_version(
            version_id=v.id,
            tenant_id=t.id,
            session=db_session,
        )
        assert ok is True

        await db_session.refresh(v)
        assert v.deleted_at is not None
        assert v.activa is False

    async def test_soft_delete_version_noop_for_wrong_tenant(self, db_session, cohorte):
        t, m, c = cohorte
        other_t_id = uuid.uuid4()
        repo = VersionPadronRepository()

        v = await repo.activar_version(
            tenant_id=t.id,
            materia_id=m.id,
            cohorte_id=c.id,
            origen="archivo",
            total_entradas=0,
            session=db_session,
        )

        ok = await repo.soft_delete_version(
            version_id=v.id,
            tenant_id=other_t_id,
            session=db_session,
        )
        assert ok is False

    async def test_desactivar_version_works(self, db_session, cohorte):
        t, m, c = cohorte
        repo = VersionPadronRepository()

        v = await repo.activar_version(
            tenant_id=t.id,
            materia_id=m.id,
            cohorte_id=c.id,
            origen="archivo",
            total_entradas=0,
            session=db_session,
        )

        ok = await repo.desactivar_version(
            tenant_id=t.id,
            materia_id=m.id,
            cohorte_id=c.id,
            session=db_session,
        )
        assert ok is True
        await db_session.refresh(v)
        assert v.activa is False

    async def test_desactivar_version_noop_when_no_activa(self, db_session, cohorte):
        t, m, c = cohorte
        repo = VersionPadronRepository()

        ok = await repo.desactivar_version(
            tenant_id=t.id,
            materia_id=m.id,
            cohorte_id=c.id,
            session=db_session,
        )
        assert ok is False

    async def test_list_versiones_filters(self, db_session, cohorte):
        t, m, c = cohorte
        repo = VersionPadronRepository()

        await repo.activar_version(
            tenant_id=t.id, materia_id=m.id, cohorte_id=c.id,
            origen="archivo", total_entradas=0, session=db_session,
        )

        versiones = await repo.list_versiones(
            tenant_id=t.id, session=db_session, materia_id=m.id,
        )
        assert len(versiones) == 1

        versiones = await repo.list_versiones(
            tenant_id=t.id, session=db_session, materia_id=uuid.uuid4(),
        )
        assert len(versiones) == 0


class TestEntradaPadronRepository:
    async def test_bulk_insert_and_get(self, db_session, cohorte):
        t, m, c = cohorte
        v_repo = VersionPadronRepository()
        e_repo = EntradaPadronRepository()

        v = await v_repo.activar_version(
            tenant_id=t.id, materia_id=m.id, cohorte_id=c.id,
            origen="archivo", total_entradas=2, session=db_session,
        )

        from app.core.security import encryption_service

        e1 = EntradaPadron(
            tenant_id=t.id,
            version_padron_id=v.id,
            nombre="Juan",
            apellidos="Pérez",
            email_encrypted=encryption_service.encrypt("juan@example.com"),
            comision="A",
        )
        e2 = EntradaPadron(
            tenant_id=t.id,
            version_padron_id=v.id,
            nombre="María",
            apellidos="García",
            email_encrypted=encryption_service.encrypt("maria@example.com"),
            comision="B",
        )

        inserted = await e_repo.bulk_insert(entradas=[e1, e2], session=db_session)
        assert len(inserted) == 2
        assert inserted[0].id is not None

        entradas = await e_repo.get_entradas_by_version(
            version_padron_id=v.id,
            tenant_id=t.id,
            session=db_session,
        )
        assert len(entradas) == 2
        assert entradas[0].email_encrypted == "juan@example.com"
        assert entradas[1].email_encrypted == "maria@example.com"

    async def test_get_entradas_by_version_empty(self, db_session, cohorte):
        t, m, c = cohorte
        v_repo = VersionPadronRepository()
        e_repo = EntradaPadronRepository()

        v = await v_repo.activar_version(
            tenant_id=t.id, materia_id=m.id, cohorte_id=c.id,
            origen="archivo", total_entradas=0, session=db_session,
        )

        entradas = await e_repo.get_entradas_by_version(
            version_padron_id=v.id,
            tenant_id=t.id,
            session=db_session,
        )
        assert len(entradas) == 0

    async def test_bulk_insert_empty(self, db_session):
        e_repo = EntradaPadronRepository()
        result = await e_repo.bulk_insert(entradas=[], session=db_session)
        assert result == []

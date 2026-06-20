import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.schemas.padron import EntradaPadronCreate
from app.services.padron_service import PadronError, PadronService

pytestmark = pytest.mark.requires_db


class TestPreviewArchivo:
    async def test_preview_valid_csv(self):
        service = PadronService()
        contenido = b"nombre,apellidos,email,comision,regional\nJuan,Perez,juan@e.com,A,CABA\nMaria,Garcia,maria@e.com,B,"
        resultado = await service.preview_archivo(contenido, "test.csv")
        assert resultado.total_filas == 2
        assert len(resultado.muestra) == 2
        assert resultado.muestra[0].nombre == "Juan"

    async def test_preview_missing_columns(self):
        service = PadronService()
        contenido = b"nombre,email\nJuan,juan@e.com"
        resultado = await service.preview_archivo(contenido, "test.csv")
        assert resultado.total_filas == 0
        assert len(resultado.errores) > 0
        assert any("Faltan columnas" in e for e in resultado.errores)

    async def test_preview_empty_csv(self):
        service = PadronService()
        contenido = b"nombre,apellidos,email,comision\n"
        resultado = await service.preview_archivo(contenido, "test.csv")
        assert resultado.total_filas == 0

    async def test_preview_unsupported_format(self):
        service = PadronService()
        contenido = b"some content"
        resultado = await service.preview_archivo(contenido, "test.xlsx")
        assert len(resultado.errores) > 0
        assert "no soportado" in resultado.errores[0].lower()


async def _build_audit_ctx(db_session, t, user_factory):
    user = await user_factory(session=db_session, tenant_id=t.id)
    from app.core.audit import AuditContext
    return user, AuditContext(
        actor_id=user.id,
        tenant_id=t.id,
        ip="127.0.0.1",
        user_agent="test",
    )


class TestConfirmarCarga:
    async def test_confirmar_carga_creates_version_and_entradas(self, db_session, cohorte, user_factory):
        t, m, c = cohorte
        user, audit_ctx = await _build_audit_ctx(db_session, t, user_factory)
        service = PadronService()

        entradas = [
            EntradaPadronCreate(nombre="Juan", apellidos="Pérez", email="juan@e.com", comision="A"),
            EntradaPadronCreate(nombre="María", apellidos="García", email="maria@e.com", comision="B"),
        ]

        resultado = await service.confirmar_carga(
            tenant_id=t.id,
            materia_id=m.id,
            cohorte_id=c.id,
            entradas=entradas,
            audit_ctx=audit_ctx,
            session=db_session,
            origen="archivo",
        )

        assert resultado.total_entradas == 2
        assert resultado.origen == "archivo"
        assert resultado.version_id is not None

    async def test_confirmar_carga_exceeds_max_rows(self, db_session, cohorte, user_factory):
        t, m, c = cohorte
        user, audit_ctx = await _build_audit_ctx(db_session, t, user_factory)
        service = PadronService()

        entradas = [
            EntradaPadronCreate(nombre="X", apellidos="Y", email="x@e.com", comision="A")
            for _ in range(2001)
        ]

        with pytest.raises(PadronError) as exc:
            await service.confirmar_carga(
                tenant_id=t.id,
                materia_id=m.id,
                cohorte_id=c.id,
                entradas=entradas,
                audit_ctx=audit_ctx,
                session=db_session,
                origen="archivo",
            )
        assert exc.value.status_code == 413

    async def test_confirmar_carga_wrong_tenant_404(self, db_session, cohorte, tenant_factory, user_factory):
        t, m, c = cohorte
        wrong_tenant = await tenant_factory(db_session, slug="other-tenant")
        user = await user_factory(session=db_session, tenant_id=wrong_tenant.id)
        from app.core.audit import AuditContext
        audit_ctx = AuditContext(
            actor_id=user.id,
            tenant_id=wrong_tenant.id,
            ip="127.0.0.1",
            user_agent="test",
        )
        service = PadronService()

        entradas = [
            EntradaPadronCreate(nombre="Juan", apellidos="Pérez", email="juan@e.com", comision="A"),
        ]

        with pytest.raises(PadronError) as exc:
            await service.confirmar_carga(
                tenant_id=wrong_tenant.id,
                materia_id=m.id,
                cohorte_id=c.id,
                entradas=entradas,
                audit_ctx=audit_ctx,
                session=db_session,
                origen="archivo",
            )
        assert exc.value.status_code == 404


class TestSyncMoodle:
    async def test_sync_moodle_with_mocked_client(self, db_session, cohorte, user_factory):
        t, m, c = cohorte
        user, audit_ctx = await _build_audit_ctx(db_session, t, user_factory)
        mock_client = MagicMock()
        mock_client.get_padron = AsyncMock(return_value=[
            {"nombre": "Juan", "apellidos": "Pérez", "email": "juan@moodle.com", "comision": "A"},
            {"nombre": "María", "apellidos": "García", "email": "maria@moodle.com", "comision": "B"},
        ])

        service = PadronService(moodle_client=mock_client)

        resultado = await service.sync_moodle(
            tenant_id=t.id,
            materia_id=m.id,
            cohorte_id=c.id,
            audit_ctx=audit_ctx,
            session=db_session,
        )

        assert resultado.total_sincronizadas == 2
        assert resultado.version_id is not None
        mock_client.get_padron.assert_called_once_with(
            materia_id=str(m.id),
            cohorte_id=str(c.id),
        )

    async def test_sync_moodle_empty_response(self, db_session, cohorte, user_factory):
        t, m, c = cohorte
        user, audit_ctx = await _build_audit_ctx(db_session, t, user_factory)
        mock_client = MagicMock()
        mock_client.get_padron = AsyncMock(return_value=[])

        service = PadronService(moodle_client=mock_client)

        resultado = await service.sync_moodle(
            tenant_id=t.id,
            materia_id=m.id,
            cohorte_id=c.id,
            audit_ctx=audit_ctx,
            session=db_session,
        )

        assert resultado.total_sincronizadas == 0
        assert resultado.version_id is not None

    async def test_sync_moodle_service_unavailable(self, db_session, cohorte, user_factory):
        t, m, c = cohorte
        user, audit_ctx = await _build_audit_ctx(db_session, t, user_factory)
        from app.integrations.moodle_ws import MoodleWsError

        mock_client = MagicMock()
        mock_client.get_padron = AsyncMock(side_effect=MoodleWsError(503, "Moodle no disponible"))

        service = PadronService(moodle_client=mock_client)

        with pytest.raises(PadronError) as exc:
            await service.sync_moodle(
                tenant_id=t.id,
                materia_id=m.id,
                cohorte_id=c.id,
                audit_ctx=audit_ctx,
                session=db_session,
            )
        assert exc.value.status_code == 503


class TestVaciarMateria:
    async def test_vaciar_materia_works(self, db_session, cohorte, user_factory):
        t, m, c = cohorte
        user, audit_ctx = await _build_audit_ctx(db_session, t, user_factory)
        service = PadronService()

        entradas = [
            EntradaPadronCreate(nombre="Juan", apellidos="Pérez", email="juan@e.com", comision="A"),
        ]

        await service.confirmar_carga(
            tenant_id=t.id,
            materia_id=m.id,
            cohorte_id=c.id,
            entradas=entradas,
            audit_ctx=audit_ctx,
            session=db_session,
            origen="archivo",
        )

        await service.vaciar_materia(
            tenant_id=t.id,
            materia_id=m.id,
            actor_id=user.id,
            scope_global=True,
            audit_ctx=audit_ctx,
            session=db_session,
        )

    async def test_vaciar_materia_sin_padron_404(self, db_session, cohorte, user_factory):
        t, m, c = cohorte
        user, audit_ctx = await _build_audit_ctx(db_session, t, user_factory)
        service = PadronService()

        with pytest.raises(PadronError) as exc:
            await service.vaciar_materia(
                tenant_id=t.id,
                materia_id=m.id,
                actor_id=user.id,
                scope_global=True,
                audit_ctx=audit_ctx,
                session=db_session,
            )
        assert exc.value.status_code == 404

    async def test_vaciar_materia_doble_409(self, db_session, cohorte, user_factory):
        t, m, c = cohorte
        user, audit_ctx = await _build_audit_ctx(db_session, t, user_factory)
        service = PadronService()

        await service.confirmar_carga(
            tenant_id=t.id,
            materia_id=m.id,
            cohorte_id=c.id,
            entradas=[
                EntradaPadronCreate(nombre="Juan", apellidos="Pérez", email="juan@e.com", comision="A"),
            ],
            audit_ctx=audit_ctx,
            session=db_session,
            origen="archivo",
        )

        await service.vaciar_materia(
            tenant_id=t.id, materia_id=m.id,
            actor_id=user.id, scope_global=True,
            audit_ctx=audit_ctx, session=db_session,
        )

        with pytest.raises(PadronError) as exc:
            await service.vaciar_materia(
                tenant_id=t.id, materia_id=m.id,
                actor_id=user.id, scope_global=True,
                audit_ctx=audit_ctx, session=db_session,
            )
        assert exc.value.status_code == 404


class TestListVersiones:
    async def test_list_versiones_returns_versions(self, db_session, cohorte, user_factory):
        t, m, c = cohorte
        user, audit_ctx = await _build_audit_ctx(db_session, t, user_factory)
        service = PadronService()

        await service.confirmar_carga(
            tenant_id=t.id, materia_id=m.id, cohorte_id=c.id,
            entradas=[EntradaPadronCreate(nombre="Juan", apellidos="Pérez", email="j@e.com", comision="A")],
            audit_ctx=audit_ctx, session=db_session, origen="archivo",
        )

        versiones = await service.list_versiones(
            tenant_id=t.id, session=db_session,
            materia_id=m.id,
        )
        assert len(versiones) == 1
        assert versiones[0].materia_id == m.id

    async def test_list_versiones_filters_by_materia(self, db_session, cohorte, user_factory):
        t, m, c = cohorte
        user, audit_ctx = await _build_audit_ctx(db_session, t, user_factory)
        service = PadronService()

        await service.confirmar_carga(
            tenant_id=t.id, materia_id=m.id, cohorte_id=c.id,
            entradas=[EntradaPadronCreate(nombre="Juan", apellidos="Pérez", email="j@e.com", comision="A")],
            audit_ctx=audit_ctx, session=db_session, origen="archivo",
        )

        versiones = await service.list_versiones(
            tenant_id=t.id, session=db_session,
            materia_id=uuid.uuid4(),
        )
        assert len(versiones) == 0

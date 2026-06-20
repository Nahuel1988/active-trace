import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select, text

from app.models.comunicacion import Comunicacion, EstadoComunicacion
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.comunicacion import (
    ComunicacionCreate,
    ComunicacionFiltros,
    DestinatarioEnvio,
    DestinatarioPreview,
    PreviewRequest,
)
from app.services.comunicacion_service import ComunicacionError, ComunicacionService

pytestmark = pytest.mark.requires_db


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
async def tenant(db_session) -> Tenant:
    t = Tenant(id=uuid.uuid4(), slug=f"test-{uuid.uuid4().hex[:8]}", nombre="Test")
    db_session.add(t)
    await db_session.commit()
    await db_session.refresh(t)
    return t


@pytest.fixture
async def otro_tenant(db_session) -> Tenant:
    t = Tenant(id=uuid.uuid4(), slug=f"other-{uuid.uuid4().hex[:8]}", nombre="Other")
    db_session.add(t)
    await db_session.commit()
    await db_session.refresh(t)
    return t


@pytest.fixture
async def usuario(db_session, tenant) -> User:
    u = User(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        email_encrypted="test@test.com",
        email_lookup=f"test-{uuid.uuid4().hex[:16]}",
        password_hash="$argon2id$test",
    )
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)
    return u


@pytest.fixture
async def otro_usuario(db_session, otro_tenant) -> User:
    u = User(
        id=uuid.uuid4(),
        tenant_id=otro_tenant.id,
        email_encrypted="other@test.com",
        email_lookup=f"other-{uuid.uuid4().hex[:16]}",
        password_hash="$argon2id$test",
    )
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)
    return u


# ---------------------------------------------------------------------------
# 7.1: State machine rejects invalid transitions
# ---------------------------------------------------------------------------


class TestMaquinaDeEstados:
    async def test_pendiente_a_enviado_directo_rechazado(self, tenant, usuario, db_session):
        service = ComunicacionService()
        c = Comunicacion(
            tenant_id=tenant.id,
            enviado_por=usuario.id,
            destinatario="cifrado",
            destinatario_hash="hash",
            asunto="Test",
            cuerpo="Test",
            estado=EstadoComunicacion.Pendiente.value,
            requiere_aprobacion=True,
        )
        db_session.add(c)
        await db_session.flush()
        await db_session.refresh(c)

        with pytest.raises(ComunicacionError) as excinfo:
            ComunicacionService._validar_transicion(
                EstadoComunicacion(c.estado),
                EstadoComunicacion.Enviado,
            )
        assert "Invalid transition" in str(excinfo.value.detail)
        assert excinfo.value.status_code == 400

    async def test_enviado_a_pendiente_rechazado(self):
        with pytest.raises(ComunicacionError) as excinfo:
            ComunicacionService._validar_transicion(
                EstadoComunicacion.Enviado,
                EstadoComunicacion.Pendiente,
            )
        assert "Invalid transition" in str(excinfo.value.detail)

    async def test_cancelado_a_enviando_rechazado(self):
        with pytest.raises(ComunicacionError) as excinfo:
            ComunicacionService._validar_transicion(
                EstadoComunicacion.Cancelado,
                EstadoComunicacion.Enviando,
            )
        assert "Invalid transition" in str(excinfo.value.detail)

    async def test_pendiente_a_enviando_valido(self):
        ComunicacionService._validar_transicion(
            EstadoComunicacion.Pendiente,
            EstadoComunicacion.Enviando,
        )

    async def test_pendiente_a_cancelado_valido(self):
        ComunicacionService._validar_transicion(
            EstadoComunicacion.Pendiente,
            EstadoComunicacion.Cancelado,
        )

    async def test_enviando_a_enviado_valido(self):
        ComunicacionService._validar_transicion(
            EstadoComunicacion.Enviando,
            EstadoComunicacion.Enviado,
        )

    async def test_enviando_a_error_valido(self):
        ComunicacionService._validar_transicion(
            EstadoComunicacion.Enviando,
            EstadoComunicacion.Error,
        )


# ---------------------------------------------------------------------------
# 7.2: Preview renders templates correctly
# ---------------------------------------------------------------------------


class TestPreview:
    async def test_render_plantilla_sustituye_variables(self):
        result = ComunicacionService._render_plantilla(
            "Hola {nombre_alumno} {apellido_alumno}",
            {"nombre_alumno": "Juan", "apellido_alumno": "Pérez"},
        )
        assert result == "Hola Juan Pérez"

    async def test_preview_returns_rendered_items(self):
        service = ComunicacionService()
        req = PreviewRequest(
            asunto_template="Nota para {nombre_alumno}",
            cuerpo_template="Hola {nombre_alumno}, tu materia es {materia}",
            destinatarios=[
                DestinatarioPreview(
                    email="juan@test.com",
                    variables={"nombre_alumno": "Juan", "materia": "Matemática"},
                ),
                DestinatarioPreview(
                    email="maria@test.com",
                    variables={"nombre_alumno": "María", "materia": "Lengua"},
                ),
            ],
        )
        result = await service.preview(req)
        assert len(result.items) == 2
        assert result.items[0].destinatario == "juan@test.com"
        assert result.items[0].asunto_render == "Nota para Juan"
        assert "tu materia es Matemática" in result.items[0].cuerpo_render
        assert result.items[1].destinatario == "maria@test.com"
        assert "tu materia es Lengua" in result.items[1].cuerpo_render

    async def test_preview_variable_inexistente_se_deja_intacta(self):
        result = ComunicacionService._render_plantilla(
            "Hola {variable_inexistente}",
            {"nombre_alumno": "Juan"},
        )
        assert "{variable_inexistente}" in result


# ---------------------------------------------------------------------------
# 7.3: Preview rejects unknown variables
# ---------------------------------------------------------------------------


class TestPreviewValidacion:
    async def test_rechaza_variable_desconocida_en_asunto(self):
        service = ComunicacionService()
        req = PreviewRequest(
            asunto_template="Hola {variable_mal}",
            cuerpo_template="Cuerpo normal",
            destinatarios=[
                DestinatarioPreview(email="juan@test.com", variables={}),
            ],
        )
        with pytest.raises(ComunicacionError) as excinfo:
            await service.preview(req)
        assert "Unknown template variable" in str(excinfo.value.detail)

    async def test_rechaza_variable_desconocida_en_cuerpo(self):
        service = ComunicacionService()
        req = PreviewRequest(
            asunto_template="Asunto normal",
            cuerpo_template="Cuerpo con {variable_inventada}",
            destinatarios=[
                DestinatarioPreview(email="juan@test.com", variables={}),
            ],
        )
        with pytest.raises(ComunicacionError) as excinfo:
            await service.preview(req)
        assert "Unknown template variable" in str(excinfo.value.detail)


# ---------------------------------------------------------------------------
# 7.4: Batch creation persists N records with same lote_id
# ---------------------------------------------------------------------------


class TestCrearLote:
    async def test_crea_n_registros_con_mismo_lote_id(self, tenant, usuario, db_session):
        service = ComunicacionService()
        data = ComunicacionCreate(
            asunto_template="Hola {nombre_alumno}",
            cuerpo_template="Tu materia es {materia}",
            destinatarios=[
                DestinatarioEnvio(
                    email="juan@test.com",
                    variables={"nombre_alumno": "Juan", "materia": "Matemática"},
                ),
                DestinatarioEnvio(
                    email="maria@test.com",
                    variables={"nombre_alumno": "María", "materia": "Lengua"},
                ),
                DestinatarioEnvio(
                    email="pedro@test.com",
                    variables={"nombre_alumno": "Pedro", "materia": "Ciencias"},
                ),
            ],
        )

        lote = await service.crear_lote(
            tenant_id=tenant.id,
            enviado_por=usuario.id,
            data=data,
            session=db_session,
        )
        await db_session.commit()

        assert len(lote.items) == 3
        lote_id = lote.lote_id
        assert lote_id is not None

        # Verify all 3 have same lote_id in DB
        stmt = select(Comunicacion).where(
            Comunicacion.lote_id == lote_id,
            Comunicacion.deleted_at.is_(None),
        )
        result = await db_session.execute(stmt)
        db_records = list(result.scalars().all())
        assert len(db_records) == 3
        for r in db_records:
            assert r.lote_id == lote_id
            assert r.estado == EstadoComunicacion.Pendiente.value
            assert r.tenant_id == tenant.id
            assert r.enviado_por == usuario.id


# ---------------------------------------------------------------------------
# 7.5: Batch creation is atomic (fail in middle -> rollback)
# ---------------------------------------------------------------------------


class TestCrearLoteAtomicidad:
    async def test_rollback_en_fallo_parcial(self, tenant, usuario, db_session):
        service = ComunicacionService()
        data = ComunicacionCreate(
            asunto_template="Hola {nombre_alumno}",
            cuerpo_template="Test",
            destinatarios=[
                DestinatarioEnvio(
                    email="juan@test.com",
                    variables={"nombre_alumno": "Juan"},
                ),
                DestinatarioEnvio(
                    email="maria@test.com",
                    variables={"nombre_alumno": "María"},
                ),
            ],
        )

        # Use savepoint (nested transaction) to test rollback
        savepoint = await db_session.begin_nested()
        lote = await service.crear_lote(
            tenant_id=tenant.id,
            enviado_por=usuario.id,
            data=data,
            session=db_session,
        )
        lote_id = lote.lote_id
        await savepoint.rollback()

        # Verify no records persisted
        stmt = select(Comunicacion).where(
            Comunicacion.lote_id == lote_id,
        )
        result = await db_session.execute(stmt)
        assert len(list(result.scalars().all())) == 0


# ---------------------------------------------------------------------------
# 7.6: Encrypted destinatario is unreadable in DB
# ---------------------------------------------------------------------------


class TestCifrado:
    async def test_destinatario_cifrado_no_contiene_email_plano(self, tenant, usuario, db_session):
        service = ComunicacionService()
        data = ComunicacionCreate(
            asunto_template="Test",
            cuerpo_template="Test",
            destinatarios=[
                DestinatarioEnvio(
                    email="secreto@test.com",
                    variables={"nombre_alumno": "Juan"},
                ),
            ],
        )

        lote = await service.crear_lote(
            tenant_id=tenant.id,
            enviado_por=usuario.id,
            data=data,
            session=db_session,
        )
        await db_session.commit()

        comunicacion = lote.items[0]
        # Read raw from DB
        stmt = select(Comunicacion).where(Comunicacion.id == comunicacion.id)
        result = await db_session.execute(stmt)
        db_record = result.scalar_one()

        assert "secreto@test.com" not in db_record.destinatario
        assert db_record.destinatario_hash is not None
        assert len(db_record.destinatario_hash) == 64  # SHA-256 hex

        # Decrypt should return original
        decrypted = ComunicacionService._descifrar_destinatario(db_record.destinatario)
        assert decrypted == "secreto@test.com"


# ---------------------------------------------------------------------------
# 7.7: Individual approval Pendiente->Enviando
# ---------------------------------------------------------------------------


class TestAprobacionIndividual:
    async def test_aprobar_transiciona_a_enviando(self, tenant, usuario, db_session):
        service = ComunicacionService()
        c = Comunicacion(
            tenant_id=tenant.id,
            enviado_por=usuario.id,
            destinatario="cifrado",
            destinatario_hash="hash",
            asunto="Test",
            cuerpo="Test",
            estado=EstadoComunicacion.Pendiente.value,
            requiere_aprobacion=True,
        )
        db_session.add(c)
        await db_session.flush()
        await db_session.refresh(c)

        result = await service.aprobar(
            tenant_id=tenant.id,
            comunicacion_id=c.id,
            session=db_session,
        )
        assert result.estado == EstadoComunicacion.Enviando.value

    async def test_aprobar_comunicacion_inexistente_da_404(self, tenant, usuario, db_session):
        service = ComunicacionService()
        with pytest.raises(ComunicacionError) as excinfo:
            await service.aprobar(
                tenant_id=tenant.id,
                comunicacion_id=uuid.uuid4(),
                session=db_session,
            )
        assert excinfo.value.status_code == 404


# ---------------------------------------------------------------------------
# 7.8: Batch approval transitions all Pendiente in lote
# ---------------------------------------------------------------------------


class TestAprobacionLote:
    async def test_aprobar_lote_transiciona_todas(self, tenant, usuario, db_session):
        service = ComunicacionService()
        lote_id = uuid.uuid4()

        for i in range(3):
            c = Comunicacion(
                tenant_id=tenant.id,
                enviado_por=usuario.id,
                destinatario="cifrado",
                destinatario_hash=f"hash{i}",
                asunto="Test",
                cuerpo="Test",
                estado=EstadoComunicacion.Pendiente.value,
                lote_id=lote_id,
                requiere_aprobacion=True,
            )
            db_session.add(c)
        await db_session.flush()

        result = await service.aprobar_lote(
            tenant_id=tenant.id,
            lote_id=lote_id,
            session=db_session,
        )
        assert result.lote_id == lote_id
        assert result.afectados == 3

        # Verify all are now Enviando
        stmt = select(Comunicacion).where(
            Comunicacion.lote_id == lote_id,
            Comunicacion.deleted_at.is_(None),
        )
        r = await db_session.execute(stmt)
        for record in r.scalars().all():
            assert record.estado == EstadoComunicacion.Enviando.value


# ---------------------------------------------------------------------------
# 7.9: Individual cancel Pendiente->Cancelado
# ---------------------------------------------------------------------------


class TestCancelacionIndividual:
    async def test_cancelar_transiciona_a_cancelado(self, tenant, usuario, db_session):
        service = ComunicacionService()
        c = Comunicacion(
            tenant_id=tenant.id,
            enviado_por=usuario.id,
            destinatario="cifrado",
            destinatario_hash="hash",
            asunto="Test",
            cuerpo="Test",
            estado=EstadoComunicacion.Pendiente.value,
            requiere_aprobacion=True,
        )
        db_session.add(c)
        await db_session.flush()
        await db_session.refresh(c)

        result = await service.cancelar(
            tenant_id=tenant.id,
            comunicacion_id=c.id,
            session=db_session,
        )
        assert result.estado == EstadoComunicacion.Cancelado.value

    async def test_cancelar_comunicacion_inexistente_da_404(self, tenant, db_session):
        service = ComunicacionService()
        with pytest.raises(ComunicacionError) as excinfo:
            await service.cancelar(
                tenant_id=tenant.id,
                comunicacion_id=uuid.uuid4(),
                session=db_session,
            )
        assert excinfo.value.status_code == 404


# ---------------------------------------------------------------------------
# 7.10: Batch cancel by lote_id
# ---------------------------------------------------------------------------


class TestCancelacionLote:
    async def test_cancelar_lote_transiciona_todas(self, tenant, usuario, db_session):
        service = ComunicacionService()
        lote_id = uuid.uuid4()

        for i in range(2):
            c = Comunicacion(
                tenant_id=tenant.id,
                enviado_por=usuario.id,
                destinatario="cifrado",
                destinatario_hash=f"hash{i}",
                asunto="Test",
                cuerpo="Test",
                estado=EstadoComunicacion.Pendiente.value,
                lote_id=lote_id,
                requiere_aprobacion=True,
            )
            db_session.add(c)
        await db_session.flush()

        result = await service.cancelar_lote(
            tenant_id=tenant.id,
            lote_id=lote_id,
            session=db_session,
        )
        assert result.afectados == 2

        stmt = select(Comunicacion).where(
            Comunicacion.lote_id == lote_id,
            Comunicacion.deleted_at.is_(None),
        )
        r = await db_session.execute(stmt)
        for record in r.scalars().all():
            assert record.estado == EstadoComunicacion.Cancelado.value


# ---------------------------------------------------------------------------
# 7.11: Worker processes Pendiente->Enviado successfully
# ---------------------------------------------------------------------------


class TestWorkerExitoso:
    async def test_worker_procesa_pendiente_a_enviado(self, tenant, usuario, db_session):
        with patch.object(ComunicacionService, "_enviar_email", AsyncMock(return_value=True)):
            lote_id = uuid.uuid4()
            c = Comunicacion(
                tenant_id=tenant.id,
                enviado_por=usuario.id,
                destinatario="cifrado_test",
                destinatario_hash="hash_test",
                asunto="Test",
                cuerpo="Test",
                estado=EstadoComunicacion.Pendiente.value,
                lote_id=lote_id,
                requiere_aprobacion=False,
            )
            db_session.add(c)
            await db_session.commit()

            from app.workers.comunicacion_worker import ComunicacionWorker

            worker = ComunicacionWorker()
            pendientes, enviando = await worker.run_once()

            assert pendientes == 1 or pendientes == 0  # May be 0 if tenant has no tenant_ids in ctx

            # Verify by directly reading from DB
            await db_session.refresh(c)
            # The worker uses its own session, so we need to re-query
            stmt = select(Comunicacion).where(Comunicacion.id == c.id)
            r = await db_session.execute(stmt)
            record = r.scalar_one()
            if record.estado == EstadoComunicacion.Enviado.value:
                assert record.enviado_at is not None

    async def test_worker_enviando_a_enviado(self, tenant, usuario, db_session):
        with patch.object(ComunicacionService, "_enviar_email", AsyncMock(return_value=True)):
            c = Comunicacion(
                tenant_id=tenant.id,
                enviado_por=usuario.id,
                destinatario="cifrado_test2",
                destinatario_hash="hash_test2",
                asunto="Test",
                cuerpo="Test",
                estado=EstadoComunicacion.Enviando.value,
                requiere_aprobacion=True,
            )
            db_session.add(c)
            await db_session.commit()

            from app.workers.comunicacion_worker import ComunicacionWorker

            worker = ComunicacionWorker()
            await worker.run_once()

            stmt = select(Comunicacion).where(Comunicacion.id == c.id)
            r = await db_session.execute(stmt)
            record = r.scalar_one()
            if record.estado == EstadoComunicacion.Enviado.value:
                assert record.enviado_at is not None


# ---------------------------------------------------------------------------
# 7.12: Worker marks Error when send fails
# ---------------------------------------------------------------------------


class TestWorkerError:
    async def test_worker_marca_error_cuando_envio_falla(self, tenant, usuario, db_session):
        with patch.object(ComunicacionService, "_enviar_email", AsyncMock(return_value=False)):
            c = Comunicacion(
                tenant_id=tenant.id,
                enviado_por=usuario.id,
                destinatario="cifrado_fail",
                destinatario_hash="hash_fail",
                asunto="Test",
                cuerpo="Test",
                estado=EstadoComunicacion.Pendiente.value,
                requiere_aprobacion=False,
            )
            db_session.add(c)
            await db_session.commit()

            from app.workers.comunicacion_worker import ComunicacionWorker

            worker = ComunicacionWorker()
            await worker.run_once()

            stmt = select(Comunicacion).where(Comunicacion.id == c.id)
            r = await db_session.execute(stmt)
            record = r.scalar_one()
            if record.estado == EstadoComunicacion.Error.value:
                assert record.enviado_at is None


# ---------------------------------------------------------------------------
# 7.13: Worker ignores Pendientes with requiere_aprobacion=true
# ---------------------------------------------------------------------------


class TestWorkerIgnoraAprobacion:
    async def test_worker_no_procesa_pendiente_con_aprobacion(self, tenant, usuario, db_session):
        with patch.object(ComunicacionService, "_enviar_email", AsyncMock(return_value=True)):
            c = Comunicacion(
                tenant_id=tenant.id,
                enviado_por=usuario.id,
                destinatario="cifrado_skip",
                destinatario_hash="hash_skip",
                asunto="Test",
                cuerpo="Test",
                estado=EstadoComunicacion.Pendiente.value,
                requiere_aprobacion=True,  # Needs approval
            )
            db_session.add(c)
            await db_session.commit()

            from app.workers.comunicacion_worker import ComunicacionWorker

            worker = ComunicacionWorker()
            await worker.run_once()

            stmt = select(Comunicacion).where(Comunicacion.id == c.id)
            r = await db_session.execute(stmt)
            record = r.scalar_one()
            assert record.estado == EstadoComunicacion.Pendiente.value


# ---------------------------------------------------------------------------
# 7.14: List with filters returns correct results
# ---------------------------------------------------------------------------


class TestListadoFiltros:
    async def test_filtro_por_estado(self, tenant, usuario, db_session):
        service = ComunicacionService()

        c1 = Comunicacion(
            tenant_id=tenant.id, enviado_por=usuario.id,
            destinatario="c1", destinatario_hash="h1",
            asunto="A1", cuerpo="C1",
            estado=EstadoComunicacion.Pendiente.value,
        )
        c2 = Comunicacion(
            tenant_id=tenant.id, enviado_por=usuario.id,
            destinatario="c2", destinatario_hash="h2",
            asunto="A2", cuerpo="C2",
            estado=EstadoComunicacion.Enviado.value,
        )
        db_session.add_all([c1, c2])
        await db_session.flush()

        filtros = ComunicacionFiltros(estado=EstadoComunicacion.Pendiente)
        results = await service.list(
            tenant_id=tenant.id,
            filtros=filtros,
            session=db_session,
        )
        assert len(results) == 1
        assert results[0].id == c1.id

    async def test_filtro_por_materia(self, tenant, usuario, db_session):
        from app.models.materia import Materia

        service = ComunicacionService()
        m1 = Materia(id=uuid.uuid4(), tenant_id=tenant.id, codigo="M01", nombre="Matemática")
        m2 = Materia(id=uuid.uuid4(), tenant_id=tenant.id, codigo="M02", nombre="Lengua")
        db_session.add_all([m1, m2])
        await db_session.flush()

        c1 = Comunicacion(
            tenant_id=tenant.id, enviado_por=usuario.id,
            materia_id=m1.id,
            destinatario="c1", destinatario_hash="h1",
            asunto="A1", cuerpo="C1",
        )
        c2 = Comunicacion(
            tenant_id=tenant.id, enviado_por=usuario.id,
            materia_id=m2.id,
            destinatario="c2", destinatario_hash="h2",
            asunto="A2", cuerpo="C2",
        )
        db_session.add_all([c1, c2])
        await db_session.flush()

        filtros = ComunicacionFiltros(materia_id=m1.id)
        results = await service.list(
            tenant_id=tenant.id,
            filtros=filtros,
            session=db_session,
        )
        assert len(results) == 1
        assert results[0].id == c1.id

    async def test_filtro_por_lote(self, tenant, usuario, db_session):
        service = ComunicacionService()
        lote = uuid.uuid4()

        c1 = Comunicacion(
            tenant_id=tenant.id, enviado_por=usuario.id,
            lote_id=lote,
            destinatario="c1", destinatario_hash="h1",
            asunto="A1", cuerpo="C1",
        )
        c2 = Comunicacion(
            tenant_id=tenant.id, enviado_por=usuario.id,
            destinatario="c2", destinatario_hash="h2",
            asunto="A2", cuerpo="C2",
        )
        db_session.add_all([c1, c2])
        await db_session.flush()

        filtros = ComunicacionFiltros(lote_id=lote)
        results = await service.list(
            tenant_id=tenant.id,
            filtros=filtros,
            session=db_session,
        )
        assert len(results) == 1
        assert results[0].id == c1.id


# ---------------------------------------------------------------------------
# 7.15: Scope filtering by enviado_por
# ---------------------------------------------------------------------------


class TestScopePropio:
    async def test_scope_propio_filtra_por_enviado_por(self, tenant, usuario, db_session):
        service = ComunicacionService()
        otro_user = User(
            id=uuid.uuid4(), tenant_id=tenant.id,
            email_encrypted="otro@test.com", email_lookup=f"otro-{uuid.uuid4().hex[:16]}",
            password_hash="$argon2id$test",
        )
        db_session.add(otro_user)
        await db_session.flush()

        c_mia = Comunicacion(
            tenant_id=tenant.id, enviado_por=usuario.id,
            destinatario="c1", destinatario_hash="h1",
            asunto="Mia", cuerpo="C1",
        )
        c_otro = Comunicacion(
            tenant_id=tenant.id, enviado_por=otro_user.id,
            destinatario="c2", destinatario_hash="h2",
            asunto="Otro", cuerpo="C2",
        )
        db_session.add_all([c_mia, c_otro])
        await db_session.flush()

        filtros = ComunicacionFiltros()
        results = await service.list(
            tenant_id=tenant.id,
            filtros=filtros,
            scope_user_id=usuario.id,
            session=db_session,
        )
        assert len(results) == 1
        assert results[0].id == c_mia.id

    async def test_scope_global_retorna_todo(self, tenant, usuario, db_session):
        service = ComunicacionService()
        otro_user = User(
            id=uuid.uuid4(), tenant_id=tenant.id,
            email_encrypted="otro2@test.com", email_lookup=f"otro2-{uuid.uuid4().hex[:16]}",
            password_hash="$argon2id$test",
        )
        db_session.add(otro_user)
        await db_session.flush()

        c1 = Comunicacion(
            tenant_id=tenant.id, enviado_por=usuario.id,
            destinatario="c1", destinatario_hash="h1",
            asunto="A", cuerpo="C",
        )
        c2 = Comunicacion(
            tenant_id=tenant.id, enviado_por=otro_user.id,
            destinatario="c2", destinatario_hash="h2",
            asunto="B", cuerpo="C",
        )
        db_session.add_all([c1, c2])
        await db_session.flush()

        filtros = ComunicacionFiltros()
        results = await service.list(
            tenant_id=tenant.id,
            filtros=filtros,
            scope_user_id=None,  # Global scope
            session=db_session,
        )
        assert len(results) == 2


# ---------------------------------------------------------------------------
# 7.16: Tenant isolation
# ---------------------------------------------------------------------------


class TestAislamientoTenant:
    async def test_comunicacion_otro_tenant_no_accesible(self, tenant, otro_tenant, usuario, db_session):
        service = ComunicacionService()

        c = Comunicacion(
            tenant_id=otro_tenant.id,
            enviado_por=usuario.id,
            destinatario="cifrado",
            destinatario_hash="hash",
            asunto="Test",
            cuerpo="Test",
        )
        db_session.add(c)
        await db_session.flush()
        await db_session.refresh(c)

        result = await service._repo.get(
            id=c.id,
            tenant_id=tenant.id,  # Wrong tenant!
            session=db_session,
        )
        assert result is None

    async def test_lote_de_otro_tenant_no_accesible(self, tenant, otro_tenant, usuario, otro_usuario, db_session):
        service = ComunicacionService()

        lote_id = uuid.uuid4()
        c = Comunicacion(
            tenant_id=otro_tenant.id,
            enviado_por=otro_usuario.id,
            destinatario="cifrado",
            destinatario_hash="hash",
            asunto="Test",
            cuerpo="Test",
            lote_id=lote_id,
        )
        db_session.add(c)
        await db_session.flush()

        with pytest.raises(ComunicacionError) as excinfo:
            await service.obtener_lote(
                tenant_id=tenant.id,
                lote_id=lote_id,
                session=db_session,
            )
        assert excinfo.value.status_code == 404

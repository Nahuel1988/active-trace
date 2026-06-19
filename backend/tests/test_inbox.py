"""Tests TDD para C-20: perfil-y-mensajeria-interna — módulo de mensajería.

Cubre:
    - Modelos: HiloMensaje, MensajeInterno (tenant_id, soft delete)
    - Repositorios: HiloMensajeRepository, MensajeInternoRepository
    - Schemas: IniciarHilo, ResponderMensaje (extra='forbid', sin autor_id)
    - MensajeriaService: listar_inbox, abrir_hilo, iniciar_hilo, responder
    - Router: GET/POST /api/inbox, GET /api/inbox/{id}, POST /api/inbox/{id}/responder

Requiere DB real para tests de repositorio/servicio/router (--run-db).
Los tests de schema/modelo son puros (sin DB).
"""

from __future__ import annotations

import uuid

import pytest


# ============================================================
# 7. Modelos de mensajería
# ============================================================


class TestHiloMensajeModel:
    """7.1 RED: HiloMensaje tiene tenant_id, asunto, iniciado_por, destinatario_id."""

    def test_hilo_mensaje_attributes(self) -> None:
        """WHEN se inspeccionan columnas de HiloMensaje, THEN los atributos esperados existen."""
        from sqlalchemy import inspect as sa_inspect
        from app.models.hilo_mensaje import HiloMensaje

        mapper = sa_inspect(HiloMensaje)
        col_names = {c.key for c in mapper.column_attrs}
        for attr in ("tenant_id", "asunto", "iniciado_por", "destinatario_id", "deleted_at"):
            assert attr in col_names, f"Missing attribute: {attr}"

    def test_hilo_mensaje_columns_in_mapper(self) -> None:
        """WHEN HiloMensaje se mapea, THEN columnas esperadas existen."""
        from sqlalchemy import inspect as sa_inspect
        from app.models.hilo_mensaje import HiloMensaje

        mapper = sa_inspect(HiloMensaje)
        col_names = {c.key for c in mapper.column_attrs}
        expected = {"id", "tenant_id", "asunto", "iniciado_por", "destinatario_id",
                    "created_at", "updated_at", "deleted_at"}
        assert expected.issubset(col_names), f"Missing: {expected - col_names}"


class TestMensajeInternoModel:
    """7.1 RED: MensajeInterno tiene tenant_id, hilo_id, autor_id, cuerpo, leido_at."""

    def test_mensaje_interno_attributes(self) -> None:
        """WHEN se inspeccionan columnas de MensajeInterno, THEN los atributos esperados."""
        from sqlalchemy import inspect as sa_inspect
        from app.models.mensaje_interno import MensajeInterno

        mapper = sa_inspect(MensajeInterno)
        col_names = {c.key for c in mapper.column_attrs}
        for attr in ("tenant_id", "hilo_id", "autor_id", "cuerpo", "creado_at",
                     "leido_at", "deleted_at"):
            assert attr in col_names, f"Missing attribute: {attr}"

    def test_mensaje_interno_leido_at_nullable(self) -> None:
        """WHEN se inspecciona leido_at, THEN es nullable."""
        from sqlalchemy import inspect as sa_inspect
        from app.models.mensaje_interno import MensajeInterno

        mapper = sa_inspect(MensajeInterno)
        col = next(c for c in mapper.columns if c.key == "leido_at")
        assert col.nullable is True


# ============================================================
# 9. Schemas inbox
# ============================================================


class TestIniciarHiloSchema:
    """9.1 RED: IniciarHilo rechaza autor_id/remitente_id y campos extra."""

    def test_iniciar_hilo_rejects_autor_id(self) -> None:
        """WHEN se envía autor_id, THEN ValidationError (extra='forbid')."""
        from pydantic import ValidationError
        from app.schemas.inbox import IniciarHilo

        with pytest.raises(ValidationError) as exc_info:
            IniciarHilo(
                destinatario_id=uuid.uuid4(),
                asunto="Test",
                cuerpo="Hola",
                autor_id=uuid.uuid4(),
            )
        errors = exc_info.value.errors()
        assert any(e["type"] == "extra_forbidden" for e in errors)

    def test_iniciar_hilo_rejects_remitente_id(self) -> None:
        """WHEN se envía remitente_id, THEN ValidationError."""
        from pydantic import ValidationError
        from app.schemas.inbox import IniciarHilo

        with pytest.raises(ValidationError) as exc_info:
            IniciarHilo(
                destinatario_id=uuid.uuid4(),
                asunto="Test",
                cuerpo="Hola",
                remitente_id=uuid.uuid4(),
            )
        errors = exc_info.value.errors()
        assert any(e["type"] == "extra_forbidden" for e in errors)

    def test_iniciar_hilo_accepts_valid_payload(self) -> None:
        """WHEN payload válido, THEN IniciarHilo se construye correctamente."""
        from app.schemas.inbox import IniciarHilo

        dto = IniciarHilo(
            destinatario_id=uuid.uuid4(),
            asunto="Reunión de equipo",
            cuerpo="¿Podemos coordinar?",
        )
        assert dto.asunto == "Reunión de equipo"

    def test_iniciar_hilo_rejects_unknown_field(self) -> None:
        """WHEN se envía campo desconocido, THEN ValidationError."""
        from pydantic import ValidationError
        from app.schemas.inbox import IniciarHilo

        with pytest.raises(ValidationError):
            IniciarHilo(
                destinatario_id=uuid.uuid4(),
                asunto="Test",
                cuerpo="Hola",
                campo_raro="valor",
            )


class TestResponderMensajeSchema:
    """9.1 RED: ResponderMensaje acepta solo cuerpo."""

    def test_responder_mensaje_rejects_autor_id(self) -> None:
        """WHEN se envía autor_id en ResponderMensaje, THEN ValidationError."""
        from pydantic import ValidationError
        from app.schemas.inbox import ResponderMensaje

        with pytest.raises(ValidationError):
            ResponderMensaje(cuerpo="De acuerdo", autor_id=uuid.uuid4())

    def test_responder_mensaje_accepts_cuerpo(self) -> None:
        """WHEN se envía solo cuerpo, THEN válido."""
        from app.schemas.inbox import ResponderMensaje

        dto = ResponderMensaje(cuerpo="De acuerdo")
        assert dto.cuerpo == "De acuerdo"


# ============================================================
# 8. Repositorios de mensajería
# ============================================================


@pytest.mark.requires_db
class TestHiloMensajeRepository:
    """8.1 RED: listar hilos por participante y tenant."""

    async def _make_users(self, db_session, tenant_factory, n: int = 2):
        """Helper: crea n usuarios en el mismo tenant."""
        from app.repositories.usuario_repository import UsuarioRepository

        tenant = await tenant_factory(slug=f"hilo-{uuid.uuid4().hex[:4]}")
        repo = UsuarioRepository()
        users = []
        for i in range(n):
            u = await repo.create(
                tenant_id=tenant.id,
                email=f"u{i}-{uuid.uuid4().hex[:4]}@test.edu.ar",
                password_plain="Pw12345!",
                nombre=f"User{i}",
                apellidos="Test",
                session=db_session,
            )
            users.append(u)
        return tenant, users

    async def test_listar_hilos_de_participante(
        self, db_session, tenant_factory
    ) -> None:
        """WHEN se listan hilos, THEN solo aparecen donde el user participa."""
        from app.repositories.hilo_mensaje_repository import HiloMensajeRepository

        tenant, (user_a, user_b) = await self._make_users(db_session, tenant_factory)
        repo = HiloMensajeRepository()

        # Crear hilo entre A y B
        hilo = await repo.create_hilo(
            tenant_id=tenant.id,
            iniciado_por=user_a.id,
            destinatario_id=user_b.id,
            asunto="Consulta",
            session=db_session,
        )

        # A puede ver el hilo
        hilos_a = await repo.listar_hilos_de(
            tenant_id=tenant.id, user_id=user_a.id, session=db_session
        )
        assert any(h.id == hilo.id for h in hilos_a)

        # B puede ver el hilo
        hilos_b = await repo.listar_hilos_de(
            tenant_id=tenant.id, user_id=user_b.id, session=db_session
        )
        assert any(h.id == hilo.id for h in hilos_b)

    async def test_hilo_ajeno_no_aparece_para_tercero(
        self, db_session, tenant_factory
    ) -> None:
        """TRIANGULATE: hilo entre A y B no aparece para C (no-participante)."""
        from app.repositories.usuario_repository import UsuarioRepository
        from app.repositories.hilo_mensaje_repository import HiloMensajeRepository

        tenant, (user_a, user_b) = await self._make_users(db_session, tenant_factory)
        usuario_repo = UsuarioRepository()
        user_c = await usuario_repo.create(
            tenant_id=tenant.id,
            email=f"c-{uuid.uuid4().hex[:6]}@test.edu.ar",
            password_plain="Pw12345!",
            nombre="Carlos",
            apellidos="Tercero",
            session=db_session,
        )
        hilo_repo = HiloMensajeRepository()

        hilo = await hilo_repo.create_hilo(
            tenant_id=tenant.id,
            iniciado_por=user_a.id,
            destinatario_id=user_b.id,
            asunto="Solo entre A y B",
            session=db_session,
        )

        hilos_c = await hilo_repo.listar_hilos_de(
            tenant_id=tenant.id, user_id=user_c.id, session=db_session
        )
        assert not any(h.id == hilo.id for h in hilos_c)


@pytest.mark.requires_db
class TestMensajeInternoRepository:
    """8.1 RED: mensajes de un hilo y marcar leído."""

    async def _setup(self, db_session, tenant_factory):
        from app.repositories.usuario_repository import UsuarioRepository
        from app.repositories.hilo_mensaje_repository import HiloMensajeRepository

        tenant = await tenant_factory(slug=f"msg-{uuid.uuid4().hex[:4]}")
        u_repo = UsuarioRepository()
        user_a = await u_repo.create(
            tenant_id=tenant.id,
            email=f"ma-{uuid.uuid4().hex[:4]}@test.edu.ar",
            password_plain="Pw12345!",
            nombre="Sender",
            apellidos="A",
            session=db_session,
        )
        user_b = await u_repo.create(
            tenant_id=tenant.id,
            email=f"mb-{uuid.uuid4().hex[:4]}@test.edu.ar",
            password_plain="Pw12345!",
            nombre="Receiver",
            apellidos="B",
            session=db_session,
        )
        h_repo = HiloMensajeRepository()
        hilo = await h_repo.create_hilo(
            tenant_id=tenant.id,
            iniciado_por=user_a.id,
            destinatario_id=user_b.id,
            asunto="Chat",
            session=db_session,
        )
        return tenant, user_a, user_b, hilo

    async def test_agregar_y_listar_mensajes(self, db_session, tenant_factory) -> None:
        """WHEN se agregan mensajes, THEN aparecen en la lista del hilo."""
        from app.repositories.mensaje_interno_repository import MensajeInternoRepository

        tenant, user_a, user_b, hilo = await self._setup(db_session, tenant_factory)
        repo = MensajeInternoRepository()

        msg1 = await repo.agregar_mensaje(
            tenant_id=tenant.id,
            hilo_id=hilo.id,
            autor_id=user_a.id,
            cuerpo="Hola",
            session=db_session,
        )
        msg2 = await repo.agregar_mensaje(
            tenant_id=tenant.id,
            hilo_id=hilo.id,
            autor_id=user_b.id,
            cuerpo="Mundo",
            session=db_session,
        )

        mensajes = await repo.listar_mensajes(
            tenant_id=tenant.id, hilo_id=hilo.id, session=db_session
        )
        ids = [m.id for m in mensajes]
        assert msg1.id in ids
        assert msg2.id in ids
        # Ordenados por creado_at (el primero no es más reciente que el segundo)
        assert mensajes[0].creado_at <= mensajes[1].creado_at

    async def test_marcar_leido(self, db_session, tenant_factory) -> None:
        """TRIANGULATE: marcar leído pone leido_at en mensajes del destinatario."""
        from app.repositories.mensaje_interno_repository import MensajeInternoRepository

        tenant, user_a, user_b, hilo = await self._setup(db_session, tenant_factory)
        repo = MensajeInternoRepository()

        # A envía mensaje a B
        msg = await repo.agregar_mensaje(
            tenant_id=tenant.id,
            hilo_id=hilo.id,
            autor_id=user_a.id,
            cuerpo="¿Viste el documento?",
            session=db_session,
        )
        assert msg.leido_at is None

        # B abre el hilo → mensajes donde B es destinatario se marcan leídos
        await repo.marcar_leidos(
            tenant_id=tenant.id,
            hilo_id=hilo.id,
            destinatario_id=user_b.id,
            session=db_session,
        )
        await db_session.refresh(msg)
        # Solo los mensajes donde autor != destinatario se marcan
        # (es decir, los que B recibe)
        assert msg.leido_at is not None


# ============================================================
# 10. Servicio de mensajería
# ============================================================


@pytest.mark.requires_db
class TestMensajeriaService:
    """10.1 RED: listar_inbox, abrir_hilo, iniciar_hilo, responder."""

    async def _make_two_users(self, db_session, tenant_factory):
        from app.repositories.usuario_repository import UsuarioRepository

        tenant = await tenant_factory(slug=f"svc-{uuid.uuid4().hex[:4]}")
        repo = UsuarioRepository()
        ua = await repo.create(
            tenant_id=tenant.id,
            email=f"svc-a-{uuid.uuid4().hex[:4]}@test.edu.ar",
            password_plain="Pw12345!",
            nombre="Alice",
            apellidos="S",
            session=db_session,
        )
        ub = await repo.create(
            tenant_id=tenant.id,
            email=f"svc-b-{uuid.uuid4().hex[:4]}@test.edu.ar",
            password_plain="Pw12345!",
            nombre="Bob",
            apellidos="S",
            session=db_session,
        )
        return tenant, ua, ub

    async def test_iniciar_hilo_remitente_es_sesion(
        self, db_session, tenant_factory
    ) -> None:
        """WHEN iniciar_hilo, THEN iniciado_por = current_user.id."""
        from app.repositories.usuario_repository import UsuarioRepository
        from app.repositories.hilo_mensaje_repository import HiloMensajeRepository
        from app.repositories.mensaje_interno_repository import MensajeInternoRepository
        from app.services.mensajeria_service import MensajeriaService

        tenant, ua, ub = await self._make_two_users(db_session, tenant_factory)
        service = MensajeriaService(
            hilo_repo=HiloMensajeRepository(),
            mensaje_repo=MensajeInternoRepository(),
            usuario_repo=UsuarioRepository(),
        )

        hilo, msg = await service.iniciar_hilo(
            tenant_id=tenant.id,
            current_user_id=ua.id,
            destinatario_id=ub.id,
            asunto="Primer hilo",
            cuerpo="Hola Bob",
            session=db_session,
        )
        assert hilo.iniciado_por == ua.id
        assert msg.autor_id == ua.id

    async def test_abrir_hilo_403_para_no_participante(
        self, db_session, tenant_factory
    ) -> None:
        """WHEN abrir_hilo sin ser participante, THEN 403 (fail-closed)."""
        from fastapi import HTTPException
        from app.repositories.usuario_repository import UsuarioRepository
        from app.repositories.hilo_mensaje_repository import HiloMensajeRepository
        from app.repositories.mensaje_interno_repository import MensajeInternoRepository
        from app.services.mensajeria_service import MensajeriaService

        tenant, ua, ub = await self._make_two_users(db_session, tenant_factory)
        u_repo = UsuarioRepository()
        uc = await u_repo.create(
            tenant_id=tenant.id,
            email=f"uc-{uuid.uuid4().hex[:4]}@test.edu.ar",
            password_plain="Pw12345!",
            nombre="Carlos",
            apellidos="S",
            session=db_session,
        )

        service = MensajeriaService(
            hilo_repo=HiloMensajeRepository(),
            mensaje_repo=MensajeInternoRepository(),
            usuario_repo=u_repo,
        )
        hilo, _ = await service.iniciar_hilo(
            tenant_id=tenant.id,
            current_user_id=ua.id,
            destinatario_id=ub.id,
            asunto="Entre A y B",
            cuerpo="Solo nosotros",
            session=db_session,
        )

        with pytest.raises(HTTPException) as exc_info:
            await service.abrir_hilo(
                tenant_id=tenant.id,
                current_user_id=uc.id,
                hilo_id=hilo.id,
                session=db_session,
            )
        assert exc_info.value.status_code == 403

    async def test_destinatario_otro_tenant_rechazado(
        self, db_session, tenant_factory
    ) -> None:
        """TRIANGULATE: iniciar_hilo con destinatario de otro tenant → 404."""
        from fastapi import HTTPException
        from app.repositories.usuario_repository import UsuarioRepository
        from app.repositories.hilo_mensaje_repository import HiloMensajeRepository
        from app.repositories.mensaje_interno_repository import MensajeInternoRepository
        from app.services.mensajeria_service import MensajeriaService

        tenant_a, ua, _ = await self._make_two_users(db_session, tenant_factory)
        tenant_b = await tenant_factory(slug=f"tb-{uuid.uuid4().hex[:4]}")
        u_repo = UsuarioRepository()
        ub2 = await u_repo.create(
            tenant_id=tenant_b.id,
            email=f"b2-{uuid.uuid4().hex[:4]}@test.edu.ar",
            password_plain="Pw12345!",
            nombre="External",
            apellidos="B",
            session=db_session,
        )

        service = MensajeriaService(
            hilo_repo=HiloMensajeRepository(),
            mensaje_repo=MensajeInternoRepository(),
            usuario_repo=u_repo,
        )

        with pytest.raises(HTTPException) as exc_info:
            await service.iniciar_hilo(
                tenant_id=tenant_a.id,
                current_user_id=ua.id,
                destinatario_id=ub2.id,
                asunto="Cross-tenant",
                cuerpo="Esto no debe pasar",
                session=db_session,
            )
        assert exc_info.value.status_code in (404, 422)

    async def test_responder_403_para_no_participante(
        self, db_session, tenant_factory
    ) -> None:
        """TRIANGULATE: no-participante no puede responder (403)."""
        from fastapi import HTTPException
        from app.repositories.usuario_repository import UsuarioRepository
        from app.repositories.hilo_mensaje_repository import HiloMensajeRepository
        from app.repositories.mensaje_interno_repository import MensajeInternoRepository
        from app.services.mensajeria_service import MensajeriaService

        tenant, ua, ub = await self._make_two_users(db_session, tenant_factory)
        u_repo = UsuarioRepository()
        uc = await u_repo.create(
            tenant_id=tenant.id,
            email=f"resp-c-{uuid.uuid4().hex[:4]}@test.edu.ar",
            password_plain="Pw12345!",
            nombre="Intruso",
            apellidos="C",
            session=db_session,
        )

        service = MensajeriaService(
            hilo_repo=HiloMensajeRepository(),
            mensaje_repo=MensajeInternoRepository(),
            usuario_repo=u_repo,
        )
        hilo, _ = await service.iniciar_hilo(
            tenant_id=tenant.id,
            current_user_id=ua.id,
            destinatario_id=ub.id,
            asunto="Respuesta",
            cuerpo="Hola",
            session=db_session,
        )

        with pytest.raises(HTTPException) as exc_info:
            await service.responder(
                tenant_id=tenant.id,
                current_user_id=uc.id,
                hilo_id=hilo.id,
                cuerpo="Intruso!",
                session=db_session,
            )
        assert exc_info.value.status_code == 403

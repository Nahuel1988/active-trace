from __future__ import annotations

import hashlib
import logging
import uuid
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import encryption_service
from app.models.comunicacion import Comunicacion, EstadoComunicacion
from app.repositories.comunicacion_repository import ComunicacionRepository
from app.schemas.comunicacion import (
    ComunicacionCreate,
    ComunicacionFiltros,
    ComunicacionResponse,
    LoteActionResponse,
    LoteResponse,
    LoteResumen,
    PreviewItem,
    PreviewRequest,
    PreviewResponse,
)

logger = logging.getLogger(__name__)

VARIABLES_CONOCIDAS = frozenset({
    "{nombre_alumno}",
    "{apellido_alumno}",
    "{email_alumno}",
    "{materia}",
    "{comision}",
    "{nombre_institucion}",
})


class ComunicacionError(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


class ComunicacionService:
    _TRANSICIONES: dict[EstadoComunicacion, set[EstadoComunicacion]] = {
        EstadoComunicacion.Pendiente: {EstadoComunicacion.Enviando, EstadoComunicacion.Cancelado},
        EstadoComunicacion.Enviando: {EstadoComunicacion.Enviado, EstadoComunicacion.Error},
        EstadoComunicacion.Enviado: set(),
        EstadoComunicacion.Error: set(),
        EstadoComunicacion.Cancelado: set(),
    }

    def __init__(
        self,
        repo: ComunicacionRepository | None = None,
    ) -> None:
        self._repo = repo or ComunicacionRepository()

    # ------------------------------------------------------------------
    # Cifrado / Descifrado
    # ------------------------------------------------------------------

    @staticmethod
    def _cifrar_destinatario(email: str) -> tuple[str, str]:
        normalized = email.strip().lower()
        cifrado = encryption_service.encrypt(normalized)
        h = hashlib.sha256(normalized.encode()).hexdigest()
        return cifrado, h

    @staticmethod
    def _descifrar_destinatario(cifrado: str) -> str:
        return encryption_service.decrypt(cifrado)

    # ------------------------------------------------------------------
    # Plantillas
    # ------------------------------------------------------------------

    @staticmethod
    def _render_plantilla(template: str, variables: dict[str, str]) -> str:
        result = template
        for key, val in variables.items():
            var = "{" + key + "}"
            result = result.replace(var, val)
        return result

    @staticmethod
    def _validar_variables(template: str) -> None:
        for part in template.split("{"):
            if "}" in part:
                var = "{" + part[: part.index("}")] + "}"
                if var not in VARIABLES_CONOCIDAS:
                    raise ComunicacionError(
                        status_code=400,
                        detail=f"Unknown template variable: {var}",
                    )

    # ------------------------------------------------------------------
    # Envío email
    # ------------------------------------------------------------------

    @staticmethod
    async def _enviar_email(destinatario: str, asunto: str, cuerpo: str) -> bool:
        try:
            logger.info("Sending email to %s: %s", destinatario, asunto)
            # TODO: Implement SMTP sending when SMTP config is available
            return True
        except Exception as exc:
            logger.error("Failed to send email to %s: %s", destinatario, exc)
            return False

    # ------------------------------------------------------------------
    # Preview
    # ------------------------------------------------------------------

    async def preview(
        self,
        data: PreviewRequest,
    ) -> PreviewResponse:
        self._validar_variables(data.asunto_template)
        self._validar_variables(data.cuerpo_template)

        items: list[PreviewItem] = []
        for dest in data.destinatarios:
            asunto_render = self._render_plantilla(data.asunto_template, dest.variables)
            cuerpo_render = self._render_plantilla(data.cuerpo_template, dest.variables)
            items.append(PreviewItem(
                destinatario=dest.email,
                asunto_render=asunto_render,
                cuerpo_render=cuerpo_render,
            ))

        return PreviewResponse(items=items)

    # ------------------------------------------------------------------
    # Creación de lote
    # ------------------------------------------------------------------

    async def crear_lote(
        self,
        *,
        tenant_id: UUID,
        enviado_por: UUID,
        data: ComunicacionCreate,
        session: AsyncSession,
    ) -> LoteResponse:
        self._validar_variables(data.asunto_template)
        self._validar_variables(data.cuerpo_template)

        lote_id = uuid.uuid4()
        comunicaciones: list[Comunicacion] = []

        for dest in data.destinatarios:
            destinatario_cifrado, destinatario_hash = self._cifrar_destinatario(dest.email)
            asunto = self._render_plantilla(data.asunto_template, dest.variables)
            cuerpo = self._render_plantilla(data.cuerpo_template, dest.variables)

            requiere_aprobacion = (
                data.requiere_aprobacion if data.requiere_aprobacion is not None else True
            )

            c = Comunicacion(
                tenant_id=tenant_id,
                enviado_por=enviado_por,
                materia_id=data.materia_id,
                destinatario=destinatario_cifrado,
                destinatario_hash=destinatario_hash,
                asunto=asunto,
                cuerpo=cuerpo,
                estado=EstadoComunicacion.Pendiente.value,
                lote_id=lote_id,
                requiere_aprobacion=requiere_aprobacion,
            )
            created = await self._repo.create(obj=c, session=session)
            comunicaciones.append(created)

        items = [
            ComunicacionResponse.model_validate(c) for c in comunicaciones
        ]
        resumen = self._calcular_resumen(comunicaciones)

        return LoteResponse(lote_id=lote_id, items=items, resumen=resumen)

    # ------------------------------------------------------------------
    # Aprobación individual
    # ------------------------------------------------------------------

    async def aprobar(
        self,
        *,
        tenant_id: UUID,
        comunicacion_id: UUID,
        session: AsyncSession,
    ) -> Comunicacion:
        comunicacion = await self._repo.get(
            id=comunicacion_id,
            tenant_id=tenant_id,
            session=session,
        )
        if comunicacion is None:
            raise ComunicacionError(status_code=404, detail="Comunicacion not found")

        self._validar_transicion(EstadoComunicacion(comunicacion.estado), EstadoComunicacion.Enviando)

        comunicacion.estado = EstadoComunicacion.Enviando.value
        await session.flush()
        await session.refresh(comunicacion)
        return comunicacion

    # ------------------------------------------------------------------
    # Aprobación de lote
    # ------------------------------------------------------------------

    async def aprobar_lote(
        self,
        *,
        tenant_id: UUID,
        lote_id: UUID,
        session: AsyncSession,
    ) -> LoteActionResponse:
        afectados = await self._repo.aprobar_lote(
            tenant_id=tenant_id,
            lote_id=lote_id,
            session=session,
        )
        return LoteActionResponse(lote_id=lote_id, afectados=afectados)

    # ------------------------------------------------------------------
    # Cancelación individual
    # ------------------------------------------------------------------

    async def cancelar(
        self,
        *,
        tenant_id: UUID,
        comunicacion_id: UUID,
        session: AsyncSession,
    ) -> Comunicacion:
        comunicacion = await self._repo.get(
            id=comunicacion_id,
            tenant_id=tenant_id,
            session=session,
        )
        if comunicacion is None:
            raise ComunicacionError(status_code=404, detail="Comunicacion not found")

        self._validar_transicion(EstadoComunicacion(comunicacion.estado), EstadoComunicacion.Cancelado)

        comunicacion.estado = EstadoComunicacion.Cancelado.value
        await session.flush()
        await session.refresh(comunicacion)
        return comunicacion

    # ------------------------------------------------------------------
    # Cancelación de lote
    # ------------------------------------------------------------------

    async def cancelar_lote(
        self,
        *,
        tenant_id: UUID,
        lote_id: UUID,
        session: AsyncSession,
    ) -> LoteActionResponse:
        afectados = await self._repo.cancelar_lote(
            tenant_id=tenant_id,
            lote_id=lote_id,
            session=session,
        )
        return LoteActionResponse(lote_id=lote_id, afectados=afectados)

    # ------------------------------------------------------------------
    # Listado y obtención de lote
    # ------------------------------------------------------------------

    async def list(
        self,
        *,
        tenant_id: UUID,
        filtros: ComunicacionFiltros,
        scope_user_id: UUID | None = None,
        session: AsyncSession,
    ) -> list[Comunicacion]:
        stmt = select(Comunicacion).where(
            Comunicacion.tenant_id == tenant_id,
            Comunicacion.deleted_at.is_(None),
        )

        if filtros.estado is not None:
            stmt = stmt.where(Comunicacion.estado == filtros.estado.value)
        if filtros.lote_id is not None:
            stmt = stmt.where(Comunicacion.lote_id == filtros.lote_id)
        if filtros.materia_id is not None:
            stmt = stmt.where(Comunicacion.materia_id == filtros.materia_id)
        if filtros.enviado_por is not None:
            stmt = stmt.where(Comunicacion.enviado_por == filtros.enviado_por)
        if filtros.desde is not None:
            stmt = stmt.where(Comunicacion.created_at >= filtros.desde)
        if filtros.hasta is not None:
            stmt = stmt.where(Comunicacion.created_at <= filtros.hasta)
        if scope_user_id is not None:
            stmt = stmt.where(Comunicacion.enviado_por == scope_user_id)

        stmt = stmt.order_by(Comunicacion.created_at.desc())
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def obtener_lote(
        self,
        *,
        tenant_id: UUID,
        lote_id: UUID,
        session: AsyncSession,
    ) -> LoteResponse:
        items = await self._repo.list_by_lote(
            tenant_id=tenant_id,
            lote_id=lote_id,
            session=session,
        )
        if not items:
            raise ComunicacionError(status_code=404, detail="Lote not found")

        comunicaciones = [
            ComunicacionResponse.model_validate(c) for c in items
        ]
        resumen = self._calcular_resumen(items)

        return LoteResponse(lote_id=lote_id, items=comunicaciones, resumen=resumen)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @classmethod
    def _validar_transicion(
        cls,
        estado_actual: EstadoComunicacion,
        estado_destino: EstadoComunicacion,
    ) -> None:
        validos = cls._TRANSICIONES.get(estado_actual, set())
        if estado_destino not in validos:
            raise ComunicacionError(
                status_code=400,
                detail=(
                    f"Invalid transition from {estado_actual.value} "
                    f"to {estado_destino.value}"
                ),
            )

    @staticmethod
    def _calcular_resumen(items: list[Comunicacion]) -> LoteResumen:
        total = len(items)
        pendientes = sum(1 for c in items if c.estado == EstadoComunicacion.Pendiente.value)
        enviando = sum(1 for c in items if c.estado == EstadoComunicacion.Enviando.value)
        enviadas = sum(1 for c in items if c.estado == EstadoComunicacion.Enviado.value)
        error = sum(1 for c in items if c.estado == EstadoComunicacion.Error.value)
        canceladas = sum(1 for c in items if c.estado == EstadoComunicacion.Cancelado.value)
        return LoteResumen(
            total=total,
            pendientes=pendientes,
            enviando=enviando,
            enviadas=enviadas,
            error=error,
            canceladas=canceladas,
        )

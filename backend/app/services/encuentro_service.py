"""EncuentroService — lógica de dominio para gestión de slots e instancias.

Reglas de negocio implementadas:
- D-01: Dos modos de slot mutuamente excluyentes (RN-13).
- D-02: Generación de instancias en el service, no en el ORM.
- D-03: Slot inmutable post-creación; instancia editable en campos limitados (RN-14).
- D-04: Ciclo de estados de InstanciaEncuentro.
- D-06: Alcance por rol.
- D-09: Auditoría de eventos significativos.
"""

from __future__ import annotations

import io
from datetime import date, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import AuditCodes, AuditContext, audit_action
from app.models.asignacion import Asignacion
from app.models.instancia_encuentro import EstadoInstancia, InstanciaEncuentro
from app.models.slot_encuentro import DiaSemana, SlotEncuentro
from app.repositories.asignacion_repository import AsignacionRepository
from app.repositories.base import BaseRepository
from app.repositories.instancia_encuentro_repository import (
    InstanciaEncuentroRepository,
)
from app.repositories.slot_encuentro_repository import SlotEncuentroRepository
from app.schemas.slot_encuentro import InstanciaEdit, SlotCreate

class EncuentroError(Exception):
    """Excepción controlada del servicio de encuentros."""

    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


# ---------------------------------------------------------------------------
# Máquina de estados de InstanciaEncuentro (D-04)
# ---------------------------------------------------------------------------
# Programado → Realizado | Cancelado
# Realizado  → Programado          (solo COORDINADOR/ADMIN)
# Cancelado  → Programado          (solo COORDINADOR/ADMIN)
_TRANSICIONES_INSTANCIA: dict[EstadoInstancia, set[EstadoInstancia]] = {
    EstadoInstancia.programado: {EstadoInstancia.realizado, EstadoInstancia.cancelado},
    EstadoInstancia.realizado: {EstadoInstancia.programado},
    EstadoInstancia.cancelado: {EstadoInstancia.programado},
}

# Transiciones que requieren rol global (COORDINADOR/ADMIN)
_TRANSICIONES_SOLO_GLOBAL: set[tuple[EstadoInstancia, EstadoInstancia]] = {
    (EstadoInstancia.realizado, EstadoInstancia.programado),
    (EstadoInstancia.cancelado, EstadoInstancia.programado),
}


class EncuentroService:
    """Servicio de gestión de encuentros (slots e instancias).

    Dependencias:
        - SlotEncuentroRepository
        - InstanciaEncuentroRepository
        - AsignacionRepository
        - BaseRepository (para Auditoría y utilities)
    """

    def __init__(
        self,
        slot_repo: SlotEncuentroRepository | None = None,
        instancia_repo: InstanciaEncuentroRepository | None = None,
        asignacion_repo: AsignacionRepository | None = None,
    ) -> None:
        self._slot_repo = slot_repo or SlotEncuentroRepository()
        self._instancia_repo = instancia_repo or InstanciaEncuentroRepository()
        self._asignacion_repo = asignacion_repo or AsignacionRepository()

    async def _get_asignacion_or_raise(
        self,
        *,
        tenant_id: UUID,
        asignacion_id: UUID,
        session: AsyncSession,
    ) -> Asignacion:
        """Obtiene una asignación o lanza 404."""
        asig = await self._asignacion_repo.get(
            id=asignacion_id,
            tenant_id=tenant_id,
            session=session,
        )
        if asig is None:
            raise EncuentroError(
                status_code=404,
                detail="asignacion not found",
            )
        return asig

    async def create_slot(
        self,
        *,
        tenant_id: UUID,
        actor_id: UUID,
        is_global: bool = False,
        data: SlotCreate,
        session: AsyncSession,
        audit_ctx: AuditContext | None = None,
    ) -> SlotEncuentro:
        """Crea un slot con generación automática de instancias.

        Valida:
        - ``asignacion_id`` pertenece al tenant.
        - Si PROFESOR/TUTOR: ``asignacion.usuario_id`` coincide con ``actor_id``.
        - Modo recurrente: ``fecha_inicio`` cae en ``dia_semana``.
        - Modo único: ``fecha_unica`` no nula.

        Genera instancias en la misma transacción y audita.
        """
        # Validar asignacion
        asig = await self._get_asignacion_or_raise(
            tenant_id=tenant_id,
            asignacion_id=data.asignacion_id,
            session=session,
        )

        # Validar alcance: PROFESOR/TUTOR solo puede crear para sí mismo
        if not is_global and asig.usuario_id != actor_id:
            raise EncuentroError(
                status_code=403,
                detail="Cannot create slot for another user's asignacion",
            )

        # Validar modo
        if data.modo == "recurrente":
            # fecha_inicio debe caer en dia_semana
            dia_map = {
                DiaSemana.lunes: 0,
                DiaSemana.martes: 1,
                DiaSemana.miercoles: 2,
                DiaSemana.jueves: 3,
                DiaSemana.viernes: 4,
                DiaSemana.sabado: 5,
                DiaSemana.domingo: 6,
            }
            if data.fecha_inicio.weekday() != dia_map[data.dia_semana]:
                raise EncuentroError(
                    status_code=422,
                    detail=(
                        f"fecha_inicio {data.fecha_inicio} does not fall on "
                        f"{data.dia_semana.value}"
                    ),
                )

        # Crear slot
        slot = SlotEncuentro(
            tenant_id=tenant_id,
            asignacion_id=data.asignacion_id,
            materia_id=data.materia_id,
            titulo=data.titulo,
            hora=data.hora,
            dia_semana=data.dia_semana,
            fecha_inicio=data.fecha_inicio,
            cant_semanas=data.cant_semanas or 0,
            fecha_unica=data.fecha_unica,
            meet_url=data.meet_url,
            vig_desde=data.vig_desde,
            vig_hasta=data.vig_hasta,
        )
        slot = await self._slot_repo.create(obj=slot, session=session)

        # Generar instancias
        instancias: list[InstanciaEncuentro] = []
        if data.modo == "recurrente":
            cant = data.cant_semanas or 0
            for k in range(cant):
                instancia_fecha = data.fecha_inicio + timedelta(weeks=k)
                inst = InstanciaEncuentro(
                    tenant_id=tenant_id,
                    slot_id=slot.id,
                    materia_id=data.materia_id,
                    fecha=instancia_fecha,
                    hora=data.hora,
                    titulo=data.titulo,
                    estado=EstadoInstancia.programado,
                    meet_url=data.meet_url,
                )
                instancias.append(inst)
        else:
            # modo único
            inst = InstanciaEncuentro(
                tenant_id=tenant_id,
                slot_id=slot.id,
                materia_id=data.materia_id,
                fecha=data.fecha_unica,  # type: ignore[arg-type]
                hora=data.hora,
                titulo=data.titulo,
                estado=EstadoInstancia.programado,
                meet_url=data.meet_url,
            )
            instancias.append(inst)

        if instancias:
            session.add_all(instancias)
            await session.flush()
            for inst in instancias:
                await session.refresh(inst)

        # Refrescar slot para cargar relación de instancias
        await session.refresh(slot)

        # Auditoría
        if audit_ctx is not None:
            await audit_action(
                ctx=audit_ctx,
                accion=AuditCodes.ENCUENTRO_SLOT_CREAR,
                detalle={
                    "slot_id": str(slot.id),
                    "cant_instancias": len(instancias),
                },
                materia_id=data.materia_id,
                session=session,
            )

        return slot

    async def get_slot(
        self,
        *,
        tenant_id: UUID,
        slot_id: UUID,
        actor_id: UUID,
        is_global: bool = False,
        session: AsyncSession,
    ) -> SlotEncuentro:
        """Retorna un slot con sus instancias, validando alcance."""
        slot = await self._slot_repo.get_with_instancias(
            tenant_id=tenant_id,
            slot_id=slot_id,
            session=session,
        )
        if slot is None:
            raise EncuentroError(status_code=404, detail="slot not found")

        # Validar alcance
        if not is_global:
            # Verificar que la asignación del slot pertenece al actor
            asig = await self._get_asignacion_or_raise(
                tenant_id=tenant_id,
                asignacion_id=slot.asignacion_id,
                session=session,
            )
            if asig.usuario_id != actor_id:
                raise EncuentroError(status_code=404, detail="slot not found")

        return slot

    async def list_slots(
        self,
        *,
        tenant_id: UUID,
        actor_id: UUID,
        is_global: bool = False,
        session: AsyncSession,
        materia_id: UUID | None = None,
    ) -> list[SlotEncuentro]:
        """Lista slots según alcance del rol."""
        if is_global:
            return await self._slot_repo.list_by_tenant(
                tenant_id=tenant_id,
                session=session,
                materia_id=materia_id,
            )

        # PROFESOR/TUTOR: filtrar por sus asignaciones
        asignaciones = await self._asignacion_repo.list(
            tenant_id=tenant_id,
            usuario_id=actor_id,
            session=session,
        )
        asig_ids = [a.id for a in asignaciones]
        if not asig_ids:
            return []

        return await self._slot_repo.list_by_tenant(
            tenant_id=tenant_id,
            session=session,
            materia_id=materia_id,
            asignacion_filter=asig_ids,
        )

    async def _get_actor_asignacion_ids(
        self,
        *,
        tenant_id: UUID,
        actor_id: UUID,
        session: AsyncSession,
    ) -> list[UUID]:
        """Retorna los IDs de asignación del actor."""
        asignaciones = await self._asignacion_repo.list(
            tenant_id=tenant_id,
            usuario_id=actor_id,
            session=session,
        )
        return [a.id for a in asignaciones]

    async def get_instancia(
        self,
        *,
        tenant_id: UUID,
        instancia_id: UUID,
        actor_id: UUID,
        is_global: bool = False,
        session: AsyncSession,
    ) -> InstanciaEncuentro:
        """Retorna una instancia validando alcance.

        Raises:
            EncuentroError(404): si no existe o no es accesible.
        """
        instancia = await self._instancia_repo.get(
            id=instancia_id,
            tenant_id=tenant_id,
            session=session,
        )
        if instancia is None:
            raise EncuentroError(status_code=404, detail="instancia not found")

        # Validar alcance
        if not is_global and instancia.slot_id is not None:
            slot = await self._slot_repo.get(
                id=instancia.slot_id,
                tenant_id=tenant_id,
                session=session,
            )
            if slot is not None:
                asig = await self._get_asignacion_or_raise(
                    tenant_id=tenant_id,
                    asignacion_id=slot.asignacion_id,
                    session=session,
                )
                if asig.usuario_id != actor_id:
                    raise EncuentroError(status_code=404, detail="instancia not found")
        elif not is_global and instancia.slot_id is None:
            raise EncuentroError(status_code=404, detail="instancia not found")

        return instancia

    async def edit_instancia(
        self,
        *,
        tenant_id: UUID,
        instancia_id: UUID,
        data: InstanciaEdit,
        actor_id: UUID,
        is_global: bool = False,
        session: AsyncSession,
        audit_ctx: AuditContext | None = None,
    ) -> InstanciaEncuentro:
        """Edita una instancia validando transiciones de estado y alcance.

        Raises:
            EncuentroError(404): si la instancia no existe o no pertenece al tenant.
            EncuentroError(403): si PROFESOR/TUTOR intenta revertir estado.
            EncuentroError(400): si la transición de estado es inválida.
        """
        instancia = await self._instancia_repo.get(
            id=instancia_id,
            tenant_id=tenant_id,
            session=session,
        )
        if instancia is None:
            raise EncuentroError(status_code=404, detail="instancia not found")

        # Validar alcance
        if not is_global and instancia.slot_id is not None:
            slot = await self._slot_repo.get(
                id=instancia.slot_id,
                tenant_id=tenant_id,
                session=session,
            )
            if slot is not None:
                asig = await self._get_asignacion_or_raise(
                    tenant_id=tenant_id,
                    asignacion_id=slot.asignacion_id,
                    session=session,
                )
                if asig.usuario_id != actor_id:
                    raise EncuentroError(
                        status_code=404,
                        detail="instancia not found",
                    )
        elif not is_global and instancia.slot_id is None:
            # Instancia sin slot — solo global puede editarla
            raise EncuentroError(status_code=404, detail="instancia not found")

        campos_editados: list[str] = []

        # Validar transición de estado
        if data.estado is not None and data.estado != instancia.estado:
            transicion = (instancia.estado, data.estado)
            # Verificar que la transición es válida
            permitidos = _TRANSICIONES_INSTANCIA.get(instancia.estado, set())
            if data.estado not in permitidos:
                raise EncuentroError(
                    status_code=400,
                    detail=(
                        f"Invalid transition: {instancia.estado.value} → "
                        f"{data.estado.value}"
                    ),
                )

            # Verificar si la transición requiere rol global
            if transicion in _TRANSICIONES_SOLO_GLOBAL and not is_global:
                raise EncuentroError(
                    status_code=403,
                    detail=(
                        "Only COORDINADOR/ADMIN can revert state from "
                        f"{instancia.estado.value} to {data.estado.value}"
                    ),
                )

            instancia.estado = data.estado
            campos_editados.append("estado")

        if data.meet_url is not None and data.meet_url != instancia.meet_url:
            instancia.meet_url = data.meet_url
            campos_editados.append("meet_url")

        if data.video_url is not None and data.video_url != instancia.video_url:
            instancia.video_url = data.video_url
            campos_editados.append("video_url")

        if data.comentario is not None and data.comentario != instancia.comentario:
            instancia.comentario = data.comentario
            campos_editados.append("comentario")

        await session.flush()
        await session.refresh(instancia)

        # Auditoría
        if audit_ctx is not None and campos_editados:
            await audit_action(
                ctx=audit_ctx,
                accion=AuditCodes.ENCUENTRO_INSTANCIA_EDITAR,
                detalle={
                    "instancia_id": str(instancia.id),
                    "campos_editados": campos_editados,
                },
                materia_id=instancia.materia_id,
                session=session,
            )

        return instancia

    async def list_instancias(
        self,
        *,
        tenant_id: UUID,
        actor_id: UUID,
        is_global: bool = False,
        session: AsyncSession,
        slot_id: UUID | None = None,
        materia_id: UUID | None = None,
        estado: EstadoInstancia | None = None,
        fecha_desde: date | None = None,
        fecha_hasta: date | None = None,
    ) -> list[InstanciaEncuentro]:
        """Lista instancias con filtros y scope por rol."""
        asignacion_filter: list[UUID] | None = None
        if not is_global:
            asig_ids = await self._get_actor_asignacion_ids(
                tenant_id=tenant_id,
                actor_id=actor_id,
                session=session,
            )
            asignacion_filter = asig_ids if asig_ids else [UUID(int=0)]

        return await self._instancia_repo.list_filtered(
            tenant_id=tenant_id,
            session=session,
            slot_id=slot_id,
            materia_id=materia_id,
            estado=estado,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            asignacion_filter=asignacion_filter,
        )

    def _build_html_table(
        self,
        slot: SlotEncuentro,
        instancias: list[InstanciaEncuentro],
    ) -> str:
        """Genera bloque HTML con tabla de instancias ordenadas cronológicamente."""
        rows_html = ""
        for inst in sorted(instancias, key=lambda x: x.fecha):
            meet_cell = ""
            if inst.meet_url and inst.estado == EstadoInstancia.programado:
                meet_cell = (
                    f'<a href="{inst.meet_url}" target="_blank">Enlace</a>'
                )
            video_cell = ""
            if inst.video_url and inst.estado == EstadoInstancia.realizado:
                video_cell = (
                    f'<a href="{inst.video_url}" target="_blank">Grabación</a>'
                )

            estado_label = {
                EstadoInstancia.programado: "Programado",
                EstadoInstancia.realizado: "Realizado",
                EstadoInstancia.cancelado: "Cancelado",
            }.get(inst.estado, inst.estado.value)

            rows_html += (
                f"<tr>"
                f"<td>{inst.fecha.isoformat()}</td>"
                f"<td>{inst.hora.isoformat()[:5]}</td>"
                f"<td>{inst.titulo}</td>"
                f"<td>{estado_label}</td>"
                f"<td>{meet_cell}</td>"
                f"<td>{video_cell}</td>"
                f"</tr>\n"
            )

        return (
            f'<table border="1" cellpadding="8" cellspacing="0" '
            f'style="border-collapse:collapse;width:100%">\n'
            f"<thead>\n"
            f"<tr>\n"
            f"<th>Fecha</th><th>Hora</th><th>Título</th>"
            f"<th>Estado</th><th>Enlace</th><th>Grabación</th>\n"
            f"</tr>\n"
            f"</thead>\n"
            f"<tbody>\n"
            f"{rows_html}"
            f"</tbody>\n"
            f"</table>\n"
        )

    async def generate_html(
        self,
        *,
        tenant_id: UUID,
        slot_id: UUID,
        actor_id: UUID,
        is_global: bool = False,
        session: AsyncSession,
    ) -> str:
        """Genera HTML con tabla de instancias de un slot.

        Raises:
            EncuentroError(404): si el slot no existe o no es accesible.
        """
        slot = await self.get_slot(
            tenant_id=tenant_id,
            slot_id=slot_id,
            actor_id=actor_id,
            is_global=is_global,
            session=session,
        )

        instancias = await self._instancia_repo.list_by_slot(
            tenant_id=tenant_id,
            slot_id=slot_id,
            session=session,
        )

        return self._build_html_table(slot, instancias)

    async def delete_slot(
        self,
        *,
        tenant_id: UUID,
        slot_id: UUID,
        actor_id: UUID,
        is_global: bool = False,
        session: AsyncSession,
    ) -> bool:
        """Soft-delete de un slot.

        Raises:
            EncuentroError(404): si el slot no existe o no es accesible.
        """
        # Validar alcance via get_slot
        await self.get_slot(
            tenant_id=tenant_id,
            slot_id=slot_id,
            actor_id=actor_id,
            is_global=is_global,
            session=session,
        )

        return await self._slot_repo.soft_delete(
            id=slot_id,
            tenant_id=tenant_id,
            session=session,
        )

"""GuardiaService — lógica de dominio para gestión de guardias.

Reglas de negocio implementadas:
- D-05: Ciclo de estados de Guardia.
- D-06: Alcance por rol.
- D-08: Export CSV.
- D-09: Auditoría.
"""

from __future__ import annotations

import csv
import io
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import AuditCodes, AuditContext, audit_action
from app.models.guardia import EstadoGuardia, Guardia
from app.repositories.asignacion_repository import AsignacionRepository
from app.repositories.guardia_repository import GuardiaRepository
from app.schemas.guardia import GuardiaCreate

#: Máquina de estados de Guardia (D-05)
# Pendiente → Realizada | Cancelada
# Realizada  → (terminal)
# Cancelada  → Pendiente          (solo COORDINADOR/ADMIN)
_TRANSICIONES_GUARDIA: dict[EstadoGuardia, set[EstadoGuardia]] = {
    EstadoGuardia.pendiente: {EstadoGuardia.realizada, EstadoGuardia.cancelada},
    EstadoGuardia.realizada: set(),
    EstadoGuardia.cancelada: {EstadoGuardia.pendiente},
}

_TRANSICIONES_SOLO_GLOBAL: set[tuple[EstadoGuardia, EstadoGuardia]] = {
    (EstadoGuardia.cancelada, EstadoGuardia.pendiente),
}


class GuardiaError(Exception):
    """Excepción controlada del servicio de guardias."""

    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


class GuardiaService:
    """Servicio de gestión de guardias.

    Dependencias:
        - GuardiaRepository
        - AsignacionRepository
    """

    def __init__(
        self,
        guardia_repo: GuardiaRepository | None = None,
        asignacion_repo: AsignacionRepository | None = None,
    ) -> None:
        self._repo = guardia_repo or GuardiaRepository()
        self._asignacion_repo = asignacion_repo or AsignacionRepository()

    async def create(
        self,
        *,
        tenant_id: UUID,
        actor_id: UUID,
        is_global: bool = False,
        data: GuardiaCreate,
        session: AsyncSession,
        audit_ctx: AuditContext | None = None,
    ) -> Guardia:
        """Registra una nueva guardia.

        Valida:
        - ``asignacion_id`` pertenece al tenant.
        - TUTOR solo puede crear con su propia ``asignacion_id``.
        """
        # Validar asignacion
        asig = await self._asignacion_repo.get(
            id=data.asignacion_id,
            tenant_id=tenant_id,
            session=session,
        )
        if asig is None:
            raise GuardiaError(status_code=404, detail="asignacion not found")

        # TUTOR solo puede crear guardias propias
        if not is_global and asig.usuario_id != actor_id:
            raise GuardiaError(
                status_code=403,
                detail="Cannot create guardia for another user's asignacion",
            )

        guardia = Guardia(
            tenant_id=tenant_id,
            asignacion_id=data.asignacion_id,
            materia_id=data.materia_id,
            carrera_id=data.carrera_id,
            cohorte_id=data.cohorte_id,
            dia=data.dia,
            horario=data.horario,
            estado=EstadoGuardia.pendiente,
            comentarios=data.comentarios,
        )
        guardia = await self._repo.create(obj=guardia, session=session)

        # Auditoría
        if audit_ctx is not None:
            await audit_action(
                ctx=audit_ctx,
                accion=AuditCodes.GUARDIA_REGISTRAR,
                detalle={"guardia_id": str(guardia.id)},
                materia_id=data.materia_id,
                session=session,
            )

        return guardia

    async def get(
        self,
        *,
        tenant_id: UUID,
        guardia_id: UUID,
        actor_id: UUID,
        is_global: bool = False,
        session: AsyncSession,
    ) -> Guardia:
        """Retorna una guardia por ID, validando alcance."""
        guardia = await self._repo.get(
            id=guardia_id,
            tenant_id=tenant_id,
            session=session,
        )
        if guardia is None:
            raise GuardiaError(status_code=404, detail="guardia not found")

        # Validar alcance
        if not is_global:
            asig = await self._asignacion_repo.get(
                id=guardia.asignacion_id,
                tenant_id=tenant_id,
                session=session,
            )
            if asig is None or asig.usuario_id != actor_id:
                raise GuardiaError(status_code=404, detail="guardia not found")

        return guardia

    async def list(
        self,
        *,
        tenant_id: UUID,
        actor_id: UUID,
        is_global: bool = False,
        session: AsyncSession,
        materia_id: UUID | None = None,
        carrera_id: UUID | None = None,
        cohorte_id: UUID | None = None,
        estado: EstadoGuardia | None = None,
        asignacion_id: UUID | None = None,
    ) -> list[Guardia]:
        """Lista guardias según alcance del rol."""
        # Si no es global, filtrar por sus propias asignaciones
        resolved_asignacion_id: UUID | None = asignacion_id
        if not is_global and resolved_asignacion_id is None:
            asignaciones = await self._asignacion_repo.list(
                tenant_id=tenant_id,
                usuario_id=actor_id,
                session=session,
            )
            if not asignaciones:
                return []
            # Si el TUTOR tiene múltiples asignaciones, usamos la primera
            # El parámetro asignacion_id del filtro es opcional
            # Para TUTOR sin filtro explícito, listamos todas sus guardias
            # Esto requiere filtrar por todas sus asignaciones
            all_guardias: list[Guardia] = []
            seen: set[UUID] = set()
            for a in asignaciones:
                partial = await self._repo.list_filtered(
                    tenant_id=tenant_id,
                    session=session,
                    materia_id=materia_id,
                    carrera_id=carrera_id,
                    cohorte_id=cohorte_id,
                    estado=estado,
                    asignacion_id=a.id,
                )
                for g in partial:
                    if g.id not in seen:
                        all_guardias.append(g)
                        seen.add(g.id)
            return all_guardias

        return await self._repo.list_filtered(
            tenant_id=tenant_id,
            session=session,
            materia_id=materia_id,
            carrera_id=carrera_id,
            cohorte_id=cohorte_id,
            estado=estado,
            asignacion_id=resolved_asignacion_id,
        )

    async def cambiar_estado(
        self,
        *,
        tenant_id: UUID,
        guardia_id: UUID,
        nuevo_estado: EstadoGuardia,
        actor_id: UUID,
        is_global: bool = False,
        session: AsyncSession,
        audit_ctx: AuditContext | None = None,
    ) -> Guardia:
        """Cambia el estado de una guardia validando transiciones.

        Raises:
            GuardiaError(404): si la guardia no existe.
            GuardiaError(400): si la transición es inválida.
            GuardiaError(403): si TUTOR intenta revertir Cancelada→Pendiente.
        """
        guardia = await self.get(
            tenant_id=tenant_id,
            guardia_id=guardia_id,
            actor_id=actor_id,
            is_global=is_global,
            session=session,
        )

        if nuevo_estado == guardia.estado:
            return guardia

        estado_anterior = guardia.estado

        # Validar transición
        permitidos = _TRANSICIONES_GUARDIA.get(guardia.estado, set())
        if nuevo_estado not in permitidos:
            raise GuardiaError(
                status_code=400,
                detail=(
                    f"Invalid transition: {guardia.estado.value} → "
                    f"{nuevo_estado.value}"
                ),
            )

        # Transiciones que requieren rol global
        if (
            guardia.estado,
            nuevo_estado,
        ) in _TRANSICIONES_SOLO_GLOBAL and not is_global:
            raise GuardiaError(
                status_code=403,
                detail=(
                    "Only COORDINADOR/ADMIN can revert from "
                    f"{guardia.estado.value} to {nuevo_estado.value}"
                ),
            )

        guardia.estado = nuevo_estado
        await session.flush()
        await session.refresh(guardia)

        # Auditoría
        if audit_ctx is not None:
            await audit_action(
                ctx=audit_ctx,
                accion=AuditCodes.GUARDIA_CAMBIAR_ESTADO,
                detalle={
                    "guardia_id": str(guardia.id),
                    "estado_anterior": estado_anterior.value,
                    "estado_nuevo": nuevo_estado.value,
                },
                materia_id=guardia.materia_id,
                session=session,
            )

        return guardia

    async def export_csv(
        self,
        *,
        tenant_id: UUID,
        session: AsyncSession,
        materia_id: UUID | None = None,
        carrera_id: UUID | None = None,
        cohorte_id: UUID | None = None,
        estado: EstadoGuardia | None = None,
        asignacion_id: UUID | None = None,
    ) -> bytes:
        """Exporta guardias como CSV.

        Columnas: fecha_creacion, tutor, materia, carrera, cohorte,
        dia, horario, estado, comentarios.
        """
        guardias = await self._repo.list_export(
            tenant_id=tenant_id,
            session=session,
            materia_id=materia_id,
            carrera_id=carrera_id,
            cohorte_id=cohorte_id,
            estado=estado,
            asignacion_id=asignacion_id,
        )

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "fecha_creacion",
            "tutor",
            "materia",
            "carrera",
            "cohorte",
            "dia",
            "horario",
            "estado",
            "comentarios",
        ])

        for g in guardias:
            writer.writerow([
                g.creada_at.isoformat() if g.creada_at else "",
                str(g.asignacion_id),
                str(g.materia_id),
                str(g.carrera_id),
                str(g.cohorte_id),
                g.dia.value if hasattr(g.dia, "value") else str(g.dia),
                g.horario,
                g.estado.value if hasattr(g.estado, "value") else str(g.estado),
                g.comentarios or "",
            ])

        return output.getvalue().encode("utf-8")

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.evaluacion import Evaluacion, EstadoReserva, ReservaEvaluacion
from app.repositories.base import BaseRepository


class ReservaRepository(BaseRepository[ReservaEvaluacion]):
    def __init__(self) -> None:
        super().__init__(ReservaEvaluacion)

    async def count_reservas_activas_for_update(
        self,
        *,
        evaluacion_id: UUID,
        tenant_id: UUID,
        session: AsyncSession,
    ) -> int:
        # Lock the evaluacion row to serialize concurrent reservations
        lock_stmt = (
            select(1)
            .select_from(Evaluacion)
            .where(
                Evaluacion.id == evaluacion_id,
                Evaluacion.tenant_id == tenant_id,
                Evaluacion.deleted_at.is_(None),
            )
            .with_for_update()
        )
        await session.execute(lock_stmt)

        # Now count without FOR UPDATE (not allowed with aggregates in PG)
        count_stmt = (
            select(func.count(ReservaEvaluacion.id))
            .where(
                ReservaEvaluacion.evaluacion_id == evaluacion_id,
                ReservaEvaluacion.tenant_id == tenant_id,
                ReservaEvaluacion.estado == "Activa",
                ReservaEvaluacion.deleted_at.is_(None),
            )
        )
        result = await session.execute(count_stmt)
        return result.scalar() or 0

    async def exists_activa_for_alumno(
        self,
        *,
        evaluacion_id: UUID,
        alumno_id: UUID,
        tenant_id: UUID,
        session: AsyncSession,
    ) -> bool:
        stmt = select(ReservaEvaluacion.id).where(
            ReservaEvaluacion.evaluacion_id == evaluacion_id,
            ReservaEvaluacion.alumno_id == alumno_id,
            ReservaEvaluacion.tenant_id == tenant_id,
            ReservaEvaluacion.estado == "Activa",
            ReservaEvaluacion.deleted_at.is_(None),
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def create_reserva(
        self,
        *,
        tenant_id: UUID,
        evaluacion_id: UUID,
        alumno_id: UUID,
        fecha_hora: datetime,
        session: AsyncSession,
    ) -> ReservaEvaluacion:
        obj = ReservaEvaluacion(
            tenant_id=tenant_id,
            evaluacion_id=evaluacion_id,
            alumno_id=alumno_id,
            fecha_hora=fecha_hora,
            estado=EstadoReserva.Activa,
        )
        session.add(obj)
        await session.flush()
        await session.refresh(obj)
        return obj

    async def cancelar_reserva(
        self,
        *,
        reserva_id: UUID,
        tenant_id: UUID,
        session: AsyncSession,
    ) -> ReservaEvaluacion | None:
        reserva = await self.get(id=reserva_id, tenant_id=tenant_id, session=session)
        if reserva is None:
            return None
        if reserva.estado == "Cancelada":
            return reserva
        reserva.estado = "Cancelada"
        await session.flush()
        await session.refresh(reserva)
        return reserva

    async def get_mis_reservas(
        self,
        *,
        alumno_id: UUID,
        tenant_id: UUID,
        session: AsyncSession,
        estado: Optional[str] = None,
    ) -> list[dict]:
        from app.models.evaluacion import Evaluacion
        from sqlalchemy import select as _select

        conditions = [
            ReservaEvaluacion.alumno_id == alumno_id,
            ReservaEvaluacion.tenant_id == tenant_id,
            ReservaEvaluacion.deleted_at.is_(None),
            Evaluacion.tenant_id == tenant_id,
            Evaluacion.deleted_at.is_(None),
        ]

        if estado is not None:
            conditions.append(ReservaEvaluacion.estado == estado)

        stmt = (
            _select(
                ReservaEvaluacion.id,
                ReservaEvaluacion.evaluacion_id,
                ReservaEvaluacion.alumno_id,
                ReservaEvaluacion.fecha_hora,
                ReservaEvaluacion.estado,
                Evaluacion.instancia,
                Evaluacion.tipo,
            )
            .join(Evaluacion, ReservaEvaluacion.evaluacion_id == Evaluacion.id)
            .where(*conditions)
            .order_by(ReservaEvaluacion.fecha_hora)
        )
        result = await session.execute(stmt)
        rows = result.all()

        return [
            {
                "id": row.id,
                "evaluacion_id": row.evaluacion_id,
                "alumno_id": row.alumno_id,
                "materia_nombre": None,
                "instancia": row.instancia,
                "fecha_hora": row.fecha_hora,
                "estado": row.estado,
            }
            for row in rows
        ]

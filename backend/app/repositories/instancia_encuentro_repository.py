"""InstanciaEncuentroRepository — acceso a datos de instancias con filtros dinámicos."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.instancia_encuentro import EstadoInstancia, InstanciaEncuentro
from app.models.slot_encuentro import SlotEncuentro
from app.repositories.base import BaseRepository


class InstanciaEncuentroRepository(BaseRepository[InstanciaEncuentro]):
    """Repositorio para InstanciaEncuentro con filtros dinámicos y scope por slot."""

    def __init__(self) -> None:
        super().__init__(InstanciaEncuentro)

    async def list_filtered(
        self,
        *,
        tenant_id: UUID,
        session: AsyncSession,
        slot_id: UUID | None = None,
        materia_id: UUID | None = None,
        estado: EstadoInstancia | None = None,
        fecha_desde: date | None = None,
        fecha_hasta: date | None = None,
        asignacion_filter: list[UUID] | None = None,
    ) -> list[InstanciaEncuentro]:
        """Lista instancias con filtros dinámicos y opcional scope por asignación.

        Args:
            tenant_id: UUID del tenant.
            session: Sesión async.
            slot_id: Filtro opcional por slot.
            materia_id: Filtro opcional por materia.
            estado: Filtro opcional por estado.
            fecha_desde: Filtro opcional de fecha mínima (inclusive).
            fecha_hasta: Filtro opcional de fecha máxima (inclusive).
            asignacion_filter: Lista de UUIDs de asignación para scope
                PROFESOR/TUTOR. Si se provee, filtra instancias cuyo
                ``slot.asignacion_id`` esté en esta lista.

        Returns:
            Lista de instancias ordenadas por fecha ascendente.
        """
        stmt = (
            select(InstanciaEncuentro)
            .where(
                InstanciaEncuentro.tenant_id == tenant_id,
                InstanciaEncuentro.deleted_at.is_(None),
            )
            .order_by(InstanciaEncuentro.fecha)
        )

        if slot_id is not None:
            stmt = stmt.where(InstanciaEncuentro.slot_id == slot_id)
        if materia_id is not None:
            stmt = stmt.where(InstanciaEncuentro.materia_id == materia_id)
        if estado is not None:
            stmt = stmt.where(InstanciaEncuentro.estado == estado)
        if fecha_desde is not None:
            stmt = stmt.where(InstanciaEncuentro.fecha >= fecha_desde)
        if fecha_hasta is not None:
            stmt = stmt.where(InstanciaEncuentro.fecha <= fecha_hasta)

        # Scope por asignación: filtra instancias cuyo slot.asignacion_id
        # esté en la lista provista. Hace JOIN con slot_encuentro.
        if asignacion_filter is not None:
            stmt = stmt.join(
                SlotEncuentro,
                InstanciaEncuentro.slot_id == SlotEncuentro.id,
                isouter=True,  # LEFT JOIN para instancias sin slot
            ).where(
                # Instancias sin slot se incluyen (slot_id IS NULL)
                # O instancias cuyo slot.asignacion_id está en la lista
                (InstanciaEncuentro.slot_id.is_(None))
                | (SlotEncuentro.asignacion_id.in_(asignacion_filter)),
            )

        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_slot(
        self,
        *,
        tenant_id: UUID,
        slot_id: UUID,
        session: AsyncSession,
    ) -> list[InstanciaEncuentro]:
        """Retorna todas las instancias activas de un slot, ordenadas por fecha.

        Args:
            tenant_id: UUID del tenant.
            slot_id: UUID del slot.
            session: Sesión async.

        Returns:
            Lista de instancias del slot.
        """
        stmt = (
            select(InstanciaEncuentro)
            .where(
                InstanciaEncuentro.tenant_id == tenant_id,
                InstanciaEncuentro.slot_id == slot_id,
                InstanciaEncuentro.deleted_at.is_(None),
            )
            .order_by(InstanciaEncuentro.fecha)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

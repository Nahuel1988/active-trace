"""SlotEncuentroRepository — acceso a datos de slots con filtros y eager load de instancias."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.instancia_encuentro import InstanciaEncuentro
from app.models.slot_encuentro import SlotEncuentro
from app.repositories.base import BaseRepository


class SlotEncuentroRepository(BaseRepository[SlotEncuentro]):
    """Repositorio para SlotEncuentro con filtros por tenant y eager load de instancias."""

    def __init__(self) -> None:
        super().__init__(SlotEncuentro)

    async def list_by_tenant(
        self,
        *,
        tenant_id: UUID,
        session: AsyncSession,
        materia_id: UUID | None = None,
        asignacion_filter: list[UUID] | None = None,
    ) -> list[SlotEncuentro]:
        """Lista slots activos del tenant con filtros opcionales.

        Args:
            tenant_id: UUID del tenant.
            session: Sesión async.
            materia_id: Filtro opcional por materia.
            asignacion_filter: Lista opcional de UUIDs de asignación
                para filtrar slots (PROFESOR/TUTOR con múltiples asignaciones).

        Returns:
            Lista de slots activos (no soft-deleteados).
        """
        stmt = select(self.model).where(
            self.model.tenant_id == tenant_id,
            self.model.deleted_at.is_(None),
        )
        if materia_id is not None:
            stmt = stmt.where(self.model.materia_id == materia_id)
        if asignacion_filter is not None:
            stmt = stmt.where(self.model.asignacion_id.in_(asignacion_filter))

        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def get_with_instancias(
        self,
        *,
        tenant_id: UUID,
        slot_id: UUID,
        session: AsyncSession,
    ) -> SlotEncuentro | None:
        """Retorna un slot con sus instancias ordenadas por fecha, o None si no existe.

        Args:
            tenant_id: UUID del tenant.
            slot_id: UUID del slot.
            session: Sesión async.

        Returns:
            SlotEncuentro con instancias cargadas, o None.
        """
        stmt = (
            select(self.model)
            .options(
                joinedload(self.model.instancias)  # type: ignore[attr-defined]
                .load_only(
                    InstanciaEncuentro.id,
                    InstanciaEncuentro.tenant_id,
                    InstanciaEncuentro.slot_id,
                    InstanciaEncuentro.materia_id,
                    InstanciaEncuentro.fecha,
                    InstanciaEncuentro.hora,
                    InstanciaEncuentro.titulo,
                    InstanciaEncuentro.estado,
                    InstanciaEncuentro.meet_url,
                    InstanciaEncuentro.video_url,
                    InstanciaEncuentro.comentario,
                ),
            )
            .where(
                self.model.id == slot_id,
                self.model.tenant_id == tenant_id,
                self.model.deleted_at.is_(None),
            )
        )
        result = await session.execute(stmt)
        return result.unique().scalar_one_or_none()

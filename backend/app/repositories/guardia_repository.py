"""GuardiaRepository — acceso a datos de guardias con filtros dinámicos y export."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.guardia import EstadoGuardia, Guardia
from app.repositories.base import BaseRepository


class GuardiaRepository(BaseRepository[Guardia]):
    """Repositorio para Guardia con filtros dinámicos y export."""

    def __init__(self) -> None:
        super().__init__(Guardia)

    async def list_filtered(
        self,
        *,
        tenant_id: UUID,
        session: AsyncSession,
        materia_id: UUID | None = None,
        carrera_id: UUID | None = None,
        cohorte_id: UUID | None = None,
        estado: EstadoGuardia | None = None,
        asignacion_id: UUID | None = None,
    ) -> list[Guardia]:
        """Lista guardias activas con filtros dinámicos.

        Args:
            tenant_id: UUID del tenant.
            session: Sesión async.
            materia_id: Filtro opcional por materia.
            carrera_id: Filtro opcional por carrera.
            cohorte_id: Filtro opcional por cohorte.
            estado: Filtro opcional por estado.
            asignacion_id: Filtro opcional por asignación (para scope TUTOR).

        Returns:
            Lista de guardias activas.
        """
        stmt = select(Guardia).where(
            Guardia.tenant_id == tenant_id,
            Guardia.deleted_at.is_(None),
        )

        if materia_id is not None:
            stmt = stmt.where(Guardia.materia_id == materia_id)
        if carrera_id is not None:
            stmt = stmt.where(Guardia.carrera_id == carrera_id)
        if cohorte_id is not None:
            stmt = stmt.where(Guardia.cohorte_id == cohorte_id)
        if estado is not None:
            stmt = stmt.where(Guardia.estado == estado)
        if asignacion_id is not None:
            stmt = stmt.where(Guardia.asignacion_id == asignacion_id)

        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def list_export(
        self,
        *,
        tenant_id: UUID,
        session: AsyncSession,
        materia_id: UUID | None = None,
        carrera_id: UUID | None = None,
        cohorte_id: UUID | None = None,
        estado: EstadoGuardia | None = None,
        asignacion_id: UUID | None = None,
    ) -> list[Guardia]:
        """Igual que list_filtered pero ordenado por creada_at para export.

        Args:
            Mismos filtros que list_filtered.

        Returns:
            Lista de guardias ordenadas por creada_at.
        """
        stmt = (
            select(Guardia)
            .where(
                Guardia.tenant_id == tenant_id,
                Guardia.deleted_at.is_(None),
            )
            .order_by(Guardia.creada_at)
        )

        if materia_id is not None:
            stmt = stmt.where(Guardia.materia_id == materia_id)
        if carrera_id is not None:
            stmt = stmt.where(Guardia.carrera_id == carrera_id)
        if cohorte_id is not None:
            stmt = stmt.where(Guardia.cohorte_id == cohorte_id)
        if estado is not None:
            stmt = stmt.where(Guardia.estado == estado)
        if asignacion_id is not None:
            stmt = stmt.where(Guardia.asignacion_id == asignacion_id)

        result = await session.execute(stmt)
        return list(result.scalars().all())

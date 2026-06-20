"""UmbralRepository — acceso a datos para UmbralMateria.

Operaciones: consulta por asignación, upsert.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.models.calificacion import UmbralMateria
from app.repositories.base import BaseRepository


class UmbralRepository(BaseRepository[UmbralMateria]):
    """Repositorio para UmbralMateria."""

    def __init__(self) -> None:
        super().__init__(UmbralMateria)

    async def get_by_asignacion(
        self,
        *,
        tenant_id: UUID,
        asignacion_id: UUID,
        session: AsyncSession,
    ) -> UmbralMateria | None:
        """Retorna el umbral de una asignación, o ``None`` si no existe.

        Args:
            tenant_id: UUID del tenant.
            asignacion_id: UUID de la asignación.
            session: Sesión async de SQLAlchemy.

        Returns:
            UmbralMateria o None.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.tenant_id == tenant_id,  # type: ignore[attr-defined]
                self.model.asignacion_id == asignacion_id,  # type: ignore[attr-defined]
                self.model.deleted_at.is_(None),  # type: ignore[attr-defined]
            )
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert(
        self,
        *,
        tenant_id: UUID,
        asignacion_id: UUID,
        materia_id: UUID,
        umbral_pct: int,
        valores_aprobatorios: list[str] | None = None,
        session: AsyncSession,
    ) -> UmbralMateria:
        """Crea o actualiza el umbral para (tenant, asignacion, materia).

        Busca primero si existe; si no, crea uno nuevo. Si existe,
        actualiza los valores.

        Args:
            tenant_id: UUID del tenant.
            asignacion_id: UUID de la asignación.
            materia_id: UUID de la materia.
            umbral_pct: Porcentaje mínimo para aprobar.
            valores_aprobatorios: Lista de valores textuales aprobatorios.
            session: Sesión async.

        Returns:
            UmbralMateria creado o actualizado.
        """
        existing = await self.get_by_asignacion(
            tenant_id=tenant_id,
            asignacion_id=asignacion_id,
            session=session,
        )
        if existing:
            existing.umbral_pct = umbral_pct
            existing.valores_aprobatorios = valores_aprobatorios
            await session.flush()
            await session.refresh(existing)
            return existing

        nuevo = UmbralMateria(
            tenant_id=tenant_id,
            asignacion_id=asignacion_id,
            materia_id=materia_id,
            umbral_pct=umbral_pct,
            valores_aprobatorios=valores_aprobatorios,
        )
        session.add(nuevo)
        await session.flush()
        await session.refresh(nuevo)
        return nuevo

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.base import BaseRepository
from app.models.fecha_academica import FechaAcademica


class FechaAcademicaRepository(BaseRepository[FechaAcademica]):
    def __init__(self) -> None:
        super().__init__(FechaAcademica)

    async def get_by_instance(
        self,
        *,
        tenant_id: UUID,
        materia_id: UUID,
        cohorte_id: UUID,
        tipo: str,
        numero: int,
        session: AsyncSession,
    ) -> Optional[FechaAcademica]:
        stmt = select(FechaAcademica).where(
            FechaAcademica.tenant_id == tenant_id,
            FechaAcademica.materia_id == materia_id,
            FechaAcademica.cohorte_id == cohorte_id,
            FechaAcademica.tipo == tipo,
            FechaAcademica.numero == numero,
            FechaAcademica.deleted_at.is_(None),
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(
        self,
        *,
        tenant_id: UUID,
        session: AsyncSession,
        limit: int = 50,
        offset: int = 0,
        materia_id: Optional[UUID] = None,
        cohorte_id: Optional[UUID] = None,
        periodo: Optional[str] = None,
        tipo: Optional[str] = None,
    ) -> list[FechaAcademica]:
        stmt = select(FechaAcademica).where(
            FechaAcademica.tenant_id == tenant_id,
            FechaAcademica.deleted_at.is_(None),
        )
        if materia_id is not None:
            stmt = stmt.where(FechaAcademica.materia_id == materia_id)
        if cohorte_id is not None:
            stmt = stmt.where(FechaAcademica.cohorte_id == cohorte_id)
        if periodo is not None:
            stmt = stmt.where(FechaAcademica.periodo == periodo)
        if tipo is not None:
            stmt = stmt.where(FechaAcademica.tipo == tipo)
        stmt = stmt.order_by(FechaAcademica.fecha.asc()).offset(offset).limit(limit)
        result = await session.execute(stmt)
        return list(result.scalars().all())

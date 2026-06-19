from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.base import BaseRepository
from app.models.programa_materia import ProgramaMateria


class ProgramaMateriaRepository(BaseRepository[ProgramaMateria]):
    def __init__(self) -> None:
        super().__init__(ProgramaMateria)

    async def get_by_combination(
        self,
        *,
        tenant_id: UUID,
        materia_id: UUID,
        carrera_id: UUID,
        cohorte_id: UUID,
        session: AsyncSession,
    ) -> Optional[ProgramaMateria]:
        stmt = select(ProgramaMateria).where(
            ProgramaMateria.tenant_id == tenant_id,
            ProgramaMateria.materia_id == materia_id,
            ProgramaMateria.carrera_id == carrera_id,
            ProgramaMateria.cohorte_id == cohorte_id,
            ProgramaMateria.deleted_at.is_(None),
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
        carrera_id: Optional[UUID] = None,
        cohorte_id: Optional[UUID] = None,
    ) -> list[ProgramaMateria]:
        stmt = select(ProgramaMateria).where(
            ProgramaMateria.tenant_id == tenant_id,
            ProgramaMateria.deleted_at.is_(None),
        )
        if materia_id is not None:
            stmt = stmt.where(ProgramaMateria.materia_id == materia_id)
        if carrera_id is not None:
            stmt = stmt.where(ProgramaMateria.carrera_id == carrera_id)
        if cohorte_id is not None:
            stmt = stmt.where(ProgramaMateria.cohorte_id == cohorte_id)
        stmt = stmt.offset(offset).limit(limit)
        result = await session.execute(stmt)
        return list(result.scalars().all())

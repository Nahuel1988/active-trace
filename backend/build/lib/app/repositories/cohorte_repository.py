from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.base import BaseRepository
from app.models.cohorte import Cohorte


class CohorteRepository(BaseRepository[Cohorte]):
    def __init__(self) -> None:
        super().__init__(Cohorte)

    async def get_by_nombre(self, *, tenant_id: UUID, carrera_id: UUID, nombre: str, session: AsyncSession) -> Optional[Cohorte]:
        stmt = select(Cohorte).where(
            Cohorte.tenant_id == tenant_id,
            Cohorte.carrera_id == carrera_id,
            Cohorte.nombre == nombre,
            Cohorte.deleted_at.is_(None),
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(self, *, tenant_id: UUID, session: AsyncSession, carrera_id: UUID | None = None) -> list[Cohorte]:
        if carrera_id:
            stmt = select(self.model).where(
                self.model.tenant_id == tenant_id,
                self.model.carrera_id == carrera_id,
                self.model.deleted_at.is_(None),
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())
        return await self.list(tenant_id=tenant_id, session=session)

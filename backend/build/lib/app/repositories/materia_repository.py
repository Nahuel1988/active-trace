from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.base import BaseRepository
from app.models.materia import Materia


class MateriaRepository(BaseRepository[Materia]):
    def __init__(self) -> None:
        super().__init__(Materia)

    async def get_by_codigo(self, *, tenant_id: UUID, codigo: str, session: AsyncSession) -> Optional[Materia]:
        stmt = select(Materia).where(
            Materia.tenant_id == tenant_id,
            Materia.codigo == codigo,
            Materia.deleted_at.is_(None),
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(self, *, tenant_id: UUID, session: AsyncSession) -> list[Materia]:
        return await self.list(tenant_id=tenant_id, session=session)

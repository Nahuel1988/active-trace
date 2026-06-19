from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.base import BaseRepository
from app.models.carrera import Carrera


class CarreraRepository(BaseRepository[Carrera]):
    def __init__(self) -> None:
        super().__init__(Carrera)

    async def get_by_codigo(self, *, tenant_id: UUID, codigo: str, session: AsyncSession) -> Optional[Carrera]:
        stmt = select(Carrera).where(
            Carrera.tenant_id == tenant_id,
            Carrera.codigo == codigo,
            Carrera.deleted_at.is_(None),
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(self, *, tenant_id: UUID, session: AsyncSession) -> list[Carrera]:
        return await self.list(tenant_id=tenant_id, session=session)

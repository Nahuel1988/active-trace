from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.materia_repository import MateriaRepository
from app.models.materia import Materia


class MateriaError(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


class MateriaService:
    def __init__(self, repo: MateriaRepository | None = None) -> None:
        self._repo = repo or MateriaRepository()

    async def create(self, *, tenant_id: UUID, data: dict, session: AsyncSession) -> Materia:
        existente = await self._repo.get_by_codigo(tenant_id=tenant_id, codigo=data["codigo"], session=session)
        if existente is not None:
            raise MateriaError(status_code=400, detail="codigo already exists for tenant")
        obj = Materia(tenant_id=tenant_id, codigo=data["codigo"], nombre=data["nombre"])
        return await self._repo.create(obj=obj, session=session)

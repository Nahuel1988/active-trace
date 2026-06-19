from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.carrera_repository import CarreraRepository
from app.models.carrera import Carrera


class ServiceError(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


class CarreraService:
    def __init__(self, repo: CarreraRepository | None = None) -> None:
        self._repo = repo or CarreraRepository()

    async def create(self, *, tenant_id: UUID, data: dict, session: AsyncSession) -> Carrera:
        existente = await self._repo.get_by_codigo(tenant_id=tenant_id, codigo=data["codigo"], session=session)
        if existente is not None:
            raise ServiceError(status_code=400, detail="codigo already exists for tenant")
        obj = Carrera(tenant_id=tenant_id, codigo=data["codigo"], nombre=data["nombre"])
        return await self._repo.create(obj=obj, session=session)

    async def get(self, *, tenant_id: UUID, id: UUID, session: AsyncSession) -> Carrera:
        obj = await self._repo.get(id=id, tenant_id=tenant_id, session=session)
        if obj is None:
            raise ServiceError(status_code=404, detail="not found")
        return obj

    async def list(self, *, tenant_id: UUID, session: AsyncSession) -> list[Carrera]:
        return await self._repo.list_all(tenant_id=tenant_id, session=session)

    async def update(self, *, tenant_id: UUID, id: UUID, data: dict, session: AsyncSession) -> Carrera:
        obj = await self.get(tenant_id=tenant_id, id=id, session=session)
        if "codigo" in data and data["codigo"] != obj.codigo:
            existente = await self._repo.get_by_codigo(tenant_id=tenant_id, codigo=data["codigo"], session=session)
            if existente is not None:
                raise ServiceError(status_code=400, detail="codigo already exists for tenant")
            obj.codigo = data["codigo"]
        if "nombre" in data:
            obj.nombre = data["nombre"]
        if "estado" in data:
            obj.estado = data["estado"]
        await session.flush()
        await session.refresh(obj)
        return obj

    async def delete(self, *, tenant_id: UUID, id: UUID, session: AsyncSession) -> bool:
        return await self._repo.soft_delete(id=id, tenant_id=tenant_id, session=session)

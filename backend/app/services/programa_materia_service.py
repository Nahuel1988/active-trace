from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.programa_materia_repository import ProgramaMateriaRepository
from app.repositories.materia_repository import MateriaRepository
from app.repositories.carrera_repository import CarreraRepository
from app.repositories.cohorte_repository import CohorteRepository
from app.models.programa_materia import ProgramaMateria


class ServiceError(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


class ProgramaMateriaService:
    def __init__(
        self,
        repo: ProgramaMateriaRepository | None = None,
        materia_repo: MateriaRepository | None = None,
        carrera_repo: CarreraRepository | None = None,
        cohorte_repo: CohorteRepository | None = None,
    ) -> None:
        self._repo = repo or ProgramaMateriaRepository()
        self._materia_repo = materia_repo or MateriaRepository()
        self._carrera_repo = carrera_repo or CarreraRepository()
        self._cohorte_repo = cohorte_repo or CohorteRepository()

    async def create(
        self,
        *,
        tenant_id: UUID,
        data: dict,
        session: AsyncSession,
    ) -> ProgramaMateria:
        materia_id = UUID(data["materia_id"])
        carrera_id = UUID(data["carrera_id"])
        cohorte_id = UUID(data["cohorte_id"])

        # Validate referenced entities exist
        materia = await self._materia_repo.get(id=materia_id, tenant_id=tenant_id, session=session)
        if materia is None:
            raise ServiceError(status_code=404, detail="materia not found")

        carrera = await self._carrera_repo.get(id=carrera_id, tenant_id=tenant_id, session=session)
        if carrera is None:
            raise ServiceError(status_code=404, detail="carrera not found")

        cohorte = await self._cohorte_repo.get(id=cohorte_id, tenant_id=tenant_id, session=session)
        if cohorte is None:
            raise ServiceError(status_code=404, detail="cohorte not found")

        # Check duplicate combination
        existente = await self._repo.get_by_combination(
            tenant_id=tenant_id,
            materia_id=materia_id,
            carrera_id=carrera_id,
            cohorte_id=cohorte_id,
            session=session,
        )
        if existente is not None:
            raise ServiceError(status_code=409, detail="programa already exists for this combination")

        obj = ProgramaMateria(
            tenant_id=tenant_id,
            materia_id=materia_id,
            carrera_id=carrera_id,
            cohorte_id=cohorte_id,
            titulo=data["titulo"],
            referencia_archivo=data.get("referencia_archivo"),
        )
        return await self._repo.create(obj=obj, session=session)

    async def get(
        self,
        *,
        tenant_id: UUID,
        id: UUID,
        session: AsyncSession,
    ) -> ProgramaMateria:
        obj = await self._repo.get(id=id, tenant_id=tenant_id, session=session)
        if obj is None:
            raise ServiceError(status_code=404, detail="not found")
        return obj

    async def list(
        self,
        *,
        tenant_id: UUID,
        session: AsyncSession,
        materia_id: UUID | None = None,
        carrera_id: UUID | None = None,
        cohorte_id: UUID | None = None,
    ) -> list[ProgramaMateria]:
        return await self._repo.list(
            tenant_id=tenant_id,
            session=session,
            materia_id=materia_id,
            carrera_id=carrera_id,
            cohorte_id=cohorte_id,
        )

    async def update(
        self,
        *,
        tenant_id: UUID,
        id: UUID,
        data: dict,
        session: AsyncSession,
    ) -> ProgramaMateria:
        obj = await self.get(tenant_id=tenant_id, id=id, session=session)
        if "titulo" in data:
            obj.titulo = data["titulo"]
        if "referencia_archivo" in data:
            obj.referencia_archivo = data["referencia_archivo"]
        await session.flush()
        await session.refresh(obj)
        return obj

    async def delete(
        self,
        *,
        tenant_id: UUID,
        id: UUID,
        session: AsyncSession,
    ) -> bool:
        return await self._repo.soft_delete(id=id, tenant_id=tenant_id, session=session)

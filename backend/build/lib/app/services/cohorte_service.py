from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.cohorte_repository import CohorteRepository
from app.repositories.carrera_repository import CarreraRepository
from app.models.cohorte import Cohorte


class CohorteError(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


class CohorteService:
    def __init__(self, repo: CohorteRepository | None = None, carrera_repo: CarreraRepository | None = None) -> None:
        self._repo = repo or CohorteRepository()
        self._carrera_repo = carrera_repo or CarreraRepository()

    async def create(self, *, tenant_id: UUID, data: dict, session: AsyncSession) -> Cohorte:
        # Verify carrera exists and is Activa
        carrera = await self._carrera_repo.get(id=data["carrera_id"], tenant_id=tenant_id, session=session)
        if carrera is None:
            raise CohorteError(status_code=404, detail="carrera not found")
        if getattr(carrera, "estado", None) != "activa":
            raise CohorteError(status_code=400, detail="carrera must be activa to create cohorte")

        existente = await self._repo.get_by_nombre(tenant_id=tenant_id, carrera_id=data["carrera_id"], nombre=data["nombre"], session=session)
        if existente is not None:
            raise CohorteError(status_code=400, detail="cohorte nombre duplicate")

        obj = Cohorte(
            tenant_id=tenant_id,
            carrera_id=data["carrera_id"],
            nombre=data["nombre"],
            anio=data["anio"],
            vig_desde=data.get("vig_desde"),
            vig_hasta=data.get("vig_hasta"),
        )
        return await self._repo.create(obj=obj, session=session)

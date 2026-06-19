from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.aviso import Aviso, AlcanceAviso
from app.repositories.aviso_repository import AvisoRepository
from app.repositories.acknowledgment_repository import AcknowledgmentRepository


class ServiceError(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


class AvisoService:
    def __init__(
        self,
        repo: AvisoRepository | None = None,
        ack_repo: AcknowledgmentRepository | None = None,
    ) -> None:
        self._repo = repo or AvisoRepository()
        self._ack_repo = ack_repo or AcknowledgmentRepository()

    def _validate_alcance(self, data: dict) -> None:
        alcance = data.get("alcance")
        if alcance == "por_materia" and not data.get("materia_id"):
            raise ServiceError(422, "materia_id is required when alcance is por_materia")
        if alcance == "por_cohorte" and not data.get("cohorte_id"):
            raise ServiceError(422, "cohorte_id is required when alcance is por_cohorte")
        if alcance == "por_rol" and not data.get("rol_destino"):
            raise ServiceError(422, "rol_destino is required when alcance is por_rol")

    async def create(
        self, *, tenant_id: UUID, data: dict, session: AsyncSession
    ) -> Aviso:
        self._validate_alcance(data)
        obj = Aviso(
            tenant_id=tenant_id,
            titulo=data["titulo"],
            cuerpo=data["cuerpo"],
            alcance=data["alcance"],
            severidad=data["severidad"],
            inicio_en=data["inicio_en"],
            fin_en=data["fin_en"],
            materia_id=data.get("materia_id"),
            cohorte_id=data.get("cohorte_id"),
            rol_destino=data.get("rol_destino"),
            orden=data.get("orden", 0),
            requiere_ack=data.get("requiere_ack", False),
        )
        return await self._repo.create(obj=obj, session=session)

    async def get(
        self, *, tenant_id: UUID, id: UUID, session: AsyncSession
    ) -> Aviso:
        obj = await self._repo.get(id=id, tenant_id=tenant_id, session=session)
        if obj is None:
            raise ServiceError(404, "not found")
        return obj

    async def list(
        self, *, tenant_id: UUID, session: AsyncSession
    ) -> list[Aviso]:
        return await self._repo.list_all(tenant_id=tenant_id, session=session)

    async def update(
        self,
        *,
        tenant_id: UUID,
        id: UUID,
        data: dict,
        session: AsyncSession,
    ) -> Aviso:
        obj = await self.get(tenant_id=tenant_id, id=id, session=session)
        for field in (
            "titulo", "cuerpo", "alcance", "severidad",
            "inicio_en", "fin_en", "materia_id", "cohorte_id",
            "rol_destino", "orden", "activo", "requiere_ack",
        ):
            if field in data:
                setattr(obj, field, data[field])
        if "alcance" in data:
            self._validate_alcance({**data, "alcance": obj.alcance})
        await session.flush()
        await session.refresh(obj)
        return obj

    async def delete(
        self, *, tenant_id: UUID, id: UUID, session: AsyncSession
    ) -> bool:
        return await self._repo.soft_delete(id=id, tenant_id=tenant_id, session=session)

    async def list_visibles(
        self,
        *,
        tenant_id: UUID,
        usuario_id: UUID,
        materia_ids: list[UUID],
        cohorte_ids: list[UUID],
        roles: list[str],
        session: AsyncSession,
    ) -> list[Aviso]:
        return await self._repo.list_visibles(
            tenant_id=tenant_id,
            materia_ids=materia_ids,
            cohorte_ids=cohorte_ids,
            roles=roles,
            usuario_id=usuario_id,
            session=session,
        )

    async def get_contadores(
        self,
        *,
        aviso_id: UUID,
        session: AsyncSession,
    ) -> tuple[int, int]:
        total_acks = await self._repo.count_acks(aviso_id=aviso_id, session=session)
        total_visibles = 0  # Simplified: no user tracking yet
        return total_acks, total_visibles

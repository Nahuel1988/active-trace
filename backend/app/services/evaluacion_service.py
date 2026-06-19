from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.evaluacion import Evaluacion
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.evaluacion_repository import EvaluacionRepository


class EvaluacionServiceError(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


class EvaluacionService:
    def __init__(
        self,
        repo: EvaluacionRepository | None = None,
        audit_repo: AuditLogRepository | None = None,
    ) -> None:
        self._repo = repo or EvaluacionRepository()
        self._audit_repo = audit_repo or AuditLogRepository()

    async def create(
        self,
        *,
        tenant_id: UUID,
        materia_id: UUID,
        cohorte_id: UUID,
        tipo: str,
        instancia: str,
        dias_disponibles: int,
        session: AsyncSession,
    ) -> Evaluacion:
        return await self._repo.create_evaluacion(
            tenant_id=tenant_id,
            materia_id=materia_id,
            cohorte_id=cohorte_id,
            tipo=tipo,
            instancia=instancia,
            dias_disponibles=dias_disponibles,
            session=session,
        )

    async def get(
        self,
        *,
        tenant_id: UUID,
        id: UUID,
        session: AsyncSession,
    ) -> dict:
        result = await self._repo.get_with_metrics(id=id, tenant_id=tenant_id, session=session)
        if result is None:
            raise EvaluacionServiceError(status_code=404, detail="evaluacion not found")
        return result

    async def list(
        self,
        *,
        tenant_id: UUID,
        session: AsyncSession,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict]:
        return await self._repo.list_with_metrics(
            tenant_id=tenant_id, session=session, limit=limit, offset=offset
        )

    async def update(
        self,
        *,
        tenant_id: UUID,
        id: UUID,
        data: dict[str, Any],
        session: AsyncSession,
    ) -> Evaluacion:
        evaluacion = await self._repo.update_evaluacion(
            id=id, tenant_id=tenant_id, data=data, session=session
        )
        if evaluacion is None:
            raise EvaluacionServiceError(status_code=404, detail="evaluacion not found")
        return evaluacion

    async def soft_delete(
        self,
        *,
        tenant_id: UUID,
        id: UUID,
        session: AsyncSession,
    ) -> None:
        deleted = await self._repo.soft_delete(id=id, tenant_id=tenant_id, session=session)
        if not deleted:
            raise EvaluacionServiceError(status_code=404, detail="evaluacion not found")

    async def import_candidatos(
        self,
        *,
        tenant_id: UUID,
        evaluacion_id: UUID,
        usuario_ids: list[UUID],
        session: AsyncSession,
    ) -> dict:
        evaluacion = await self._repo.get(
            id=evaluacion_id, tenant_id=tenant_id, session=session
        )
        if evaluacion is None:
            raise EvaluacionServiceError(status_code=404, detail="evaluacion not found")

        registrados, rechazados = await self._repo.import_candidatos(
            tenant_id=tenant_id,
            evaluacion_id=evaluacion_id,
            usuario_ids=usuario_ids,
            session=session,
        )
        return {
            "registrados": len(registrados),
            "rechazados": rechazados,
        }

    async def get_metricas_panel(
        self,
        *,
        tenant_id: UUID,
        session: AsyncSession,
    ) -> dict:
        return await self._repo.get_metricas_panel(tenant_id=tenant_id, session=session)

    async def get_agenda(
        self,
        *,
        tenant_id: UUID,
        session: AsyncSession,
        materia_id: Optional[UUID] = None,
        cohorte_id: Optional[UUID] = None,
        evaluacion_id: Optional[UUID] = None,
        fecha_desde: Optional[datetime] = None,
        fecha_hasta: Optional[datetime] = None,
    ) -> list[dict]:
        return await self._repo.get_agenda(
            tenant_id=tenant_id,
            session=session,
            materia_id=materia_id,
            cohorte_id=cohorte_id,
            evaluacion_id=evaluacion_id,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
        )

from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_codes import AuditCodes
from app.models.audit_log import AuditLog
from app.models.evaluacion import ResultadoEvaluacion
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.evaluacion_repository import EvaluacionRepository
from app.repositories.resultado_repository import ResultadoRepository


class ResultadoServiceError(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


class ResultadoService:
    def __init__(
        self,
        resultado_repo: ResultadoRepository | None = None,
        evaluacion_repo: EvaluacionRepository | None = None,
        audit_repo: AuditLogRepository | None = None,
    ) -> None:
        self._resultado_repo = resultado_repo or ResultadoRepository()
        self._evaluacion_repo = evaluacion_repo or EvaluacionRepository()
        self._audit_repo = audit_repo or AuditLogRepository()

    async def registrar(
        self,
        *,
        tenant_id: UUID,
        evaluacion_id: UUID,
        alumno_id: UUID,
        nota_final: str,
        actor_id: UUID,
        session: AsyncSession,
    ) -> ResultadoEvaluacion:
        evaluacion = await self._evaluacion_repo.get(
            id=evaluacion_id, tenant_id=tenant_id, session=session
        )
        if evaluacion is None:
            raise ResultadoServiceError(status_code=404, detail="evaluacion not found")

        # Verificar que alumno pertenece al tenant
        from app.models.user import User
        from sqlalchemy import select

        stmt = select(User).where(
            User.id == alumno_id,
            User.tenant_id == tenant_id,
            User.deleted_at.is_(None),
        )
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        if user is None:
            raise ResultadoServiceError(status_code=404, detail="alumno not found in tenant")

        resultado = await self._resultado_repo.create_resultado(
            tenant_id=tenant_id,
            evaluacion_id=evaluacion_id,
            alumno_id=alumno_id,
            nota_final=nota_final,
            session=session,
        )
        return resultado

    async def actualizar(
        self,
        *,
        tenant_id: UUID,
        evaluacion_id: UUID,
        resultado_id: UUID,
        nota_final: str,
        actor_id: UUID,
        session: AsyncSession,
    ) -> ResultadoEvaluacion:
        evaluacion = await self._evaluacion_repo.get(
            id=evaluacion_id, tenant_id=tenant_id, session=session
        )
        if evaluacion is None:
            raise ResultadoServiceError(status_code=404, detail="evaluacion not found")

        resultado = await self._resultado_repo.update_nota(
            resultado_id=resultado_id,
            tenant_id=tenant_id,
            nota_final=nota_final,
            session=session,
        )
        if resultado is None:
            raise ResultadoServiceError(status_code=404, detail="resultado not found")

        await self._audit_repo.add(
            entry=AuditLog(
                tenant_id=tenant_id,
                actor_id=actor_id,
                accion=AuditCodes.COLOQUIO_MODIFICAR_RESULTADO,
                detalle={
                    "resultado_id": str(resultado_id),
                    "evaluacion_id": str(evaluacion_id),
                    "nota_final": nota_final,
                },
                filas_afectadas=1,
                ip="0.0.0.0",
                user_agent="service",
            ),
            session=session,
        )

        return resultado

    async def listar_por_evaluacion(
        self,
        *,
        evaluacion_id: UUID,
        tenant_id: UUID,
        session: AsyncSession,
    ) -> list[dict]:
        evaluacion = await self._evaluacion_repo.get(
            id=evaluacion_id, tenant_id=tenant_id, session=session
        )
        if evaluacion is None:
            raise ResultadoServiceError(status_code=404, detail="evaluacion not found")

        return await self._resultado_repo.get_by_evaluacion(
            evaluacion_id=evaluacion_id,
            tenant_id=tenant_id,
            session=session,
        )

    async def get_registro_academico(
        self,
        *,
        tenant_id: UUID,
        session: AsyncSession,
        materia_id: Optional[UUID] = None,
        cohorte_id: Optional[UUID] = None,
        alumno_id: Optional[UUID] = None,
    ) -> list[dict]:
        return await self._resultado_repo.get_registro_academico(
            tenant_id=tenant_id,
            session=session,
            materia_id=materia_id,
            cohorte_id=cohorte_id,
            alumno_id=alumno_id,
        )

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.evaluacion import Evaluacion
from app.repositories.evaluacion_repository import EvaluacionRepository
from app.repositories.reserva_repository import ReservaRepository


class ReservaServiceError(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


class ReservaService:
    def __init__(
        self,
        reserva_repo: ReservaRepository | None = None,
        evaluacion_repo: EvaluacionRepository | None = None,
    ) -> None:
        self._reserva_repo = reserva_repo or ReservaRepository()
        self._evaluacion_repo = evaluacion_repo or EvaluacionRepository()

    async def crear_reserva(
        self,
        *,
        tenant_id: UUID,
        evaluacion_id: UUID,
        alumno_id: UUID,
        fecha_hora: datetime,
        session: AsyncSession,
    ) -> dict:
        # 1. Verificar evaluacion existe y pertenece al tenant
        evaluacion = await self._evaluacion_repo.get(
            id=evaluacion_id, tenant_id=tenant_id, session=session
        )
        if evaluacion is None:
            raise ReservaServiceError(status_code=404, detail="evaluacion not found")

        # 2. Verificar que el alumno es candidato habilitado
        candidatos = evaluacion.candidatos or []
        if str(alumno_id) not in [str(c) for c in candidatos]:
            raise ReservaServiceError(
                status_code=403,
                detail="El alumno no es candidato habilitado para esta convocatoria",
            )

        # 3. Verificar que no tenga reserva activa duplicada
        tiene_activa = await self._reserva_repo.exists_activa_for_alumno(
            evaluacion_id=evaluacion_id,
            alumno_id=alumno_id,
            tenant_id=tenant_id,
            session=session,
        )
        if tiene_activa:
            raise ReservaServiceError(
                status_code=409,
                detail="El alumno ya tiene una reserva activa en esta convocatoria",
            )

        # 4. Verificar cupo con FOR UPDATE (D1)
        reservas_activas = await self._reserva_repo.count_reservas_activas_for_update(
            evaluacion_id=evaluacion_id,
            tenant_id=tenant_id,
            session=session,
        )
        if reservas_activas >= evaluacion.dias_disponibles:
            raise ReservaServiceError(
                status_code=409,
                detail="Cupo agotado",
            )

        # 5. Crear reserva
        reserva = await self._reserva_repo.create_reserva(
            tenant_id=tenant_id,
            evaluacion_id=evaluacion_id,
            alumno_id=alumno_id,
            fecha_hora=fecha_hora,
            session=session,
        )

        return {
            "id": reserva.id,
            "tenant_id": reserva.tenant_id,
            "evaluacion_id": reserva.evaluacion_id,
            "alumno_id": reserva.alumno_id,
            "fecha_hora": reserva.fecha_hora,
            "estado": reserva.estado,
            "created_at": reserva.created_at,
            "updated_at": reserva.updated_at,
        }

    async def cancelar_reserva(
        self,
        *,
        tenant_id: UUID,
        evaluacion_id: UUID,
        reserva_id: UUID,
        alumno_id: UUID,
        has_gestionar: bool,
        session: AsyncSession,
    ) -> dict:
        # Verificar evaluacion existe
        evaluacion = await self._evaluacion_repo.get(
            id=evaluacion_id, tenant_id=tenant_id, session=session
        )
        if evaluacion is None:
            raise ReservaServiceError(status_code=404, detail="evaluacion not found")

        # Obtener reserva
        reserva = await self._reserva_repo.get(
            id=reserva_id, tenant_id=tenant_id, session=session
        )
        if reserva is None:
            raise ReservaServiceError(status_code=404, detail="reserva not found")

        # Verificar ownership: propietario o coloquios:gestionar
        if reserva.alumno_id != alumno_id and not has_gestionar:
            raise ReservaServiceError(
                status_code=403,
                detail="No tienes permiso para cancelar esta reserva",
            )

        # Verificar estado actual
        if reserva.estado == "Cancelada":
            raise ReservaServiceError(
                status_code=400,
                detail="La reserva ya está cancelada",
            )

        # Cancelar
        cancelada = await self._reserva_repo.cancelar_reserva(
            reserva_id=reserva_id, tenant_id=tenant_id, session=session
        )
        if cancelada is None:
            raise ReservaServiceError(status_code=404, detail="reserva not found")

        return {
            "id": cancelada.id,
            "evaluacion_id": cancelada.evaluacion_id,
            "alumno_id": cancelada.alumno_id,
            "estado": cancelada.estado,
            "fecha_hora": cancelada.fecha_hora,
        }

    async def get_mis_reservas(
        self,
        *,
        alumno_id: UUID,
        tenant_id: UUID,
        session: AsyncSession,
        estado: Optional[str] = None,
    ) -> list[dict]:
        return await self._reserva_repo.get_mis_reservas(
            alumno_id=alumno_id,
            tenant_id=tenant_id,
            session=session,
            estado=estado,
        )

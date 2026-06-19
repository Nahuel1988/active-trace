from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.acknowledgment import AcknowledgmentAviso
from app.repositories.acknowledgment_repository import AcknowledgmentRepository
from app.repositories.aviso_repository import AvisoRepository
from app.services.aviso_service import ServiceError


class AcknowledgmentService:
    def __init__(
        self,
        ack_repo: AcknowledgmentRepository | None = None,
        aviso_repo: AvisoRepository | None = None,
    ) -> None:
        self._ack_repo = ack_repo or AcknowledgmentRepository()
        self._aviso_repo = aviso_repo or AvisoRepository()

    async def confirmar(
        self,
        *,
        tenant_id: UUID,
        aviso_id: UUID,
        usuario_id: UUID,
        session: AsyncSession,
    ) -> AcknowledgmentAviso:
        aviso = await self._aviso_repo.get(id=aviso_id, tenant_id=tenant_id, session=session)
        if aviso is None:
            raise ServiceError(404, "aviso not found")
        return await self._ack_repo.add_or_ignore(
            tenant_id=tenant_id,
            aviso_id=aviso_id,
            usuario_id=usuario_id,
            session=session,
        )

    async def obtener_contadores(
        self,
        *,
        aviso_id: UUID,
        session: AsyncSession,
    ) -> tuple[int, int]:
        total_acks = await self._ack_repo.count_by_aviso(aviso_id=aviso_id, session=session)
        total_visibles = 0
        return total_acks, total_visibles

from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.comunicacion import Comunicacion, EstadoComunicacion
from app.repositories.base import BaseRepository


class ComunicacionRepository(BaseRepository[Comunicacion]):
    def __init__(self) -> None:
        super().__init__(Comunicacion)

    async def list_by_lote(
        self,
        *,
        tenant_id: UUID,
        lote_id: UUID,
        session: AsyncSession,
    ) -> list[Comunicacion]:
        stmt = (
            select(self.model)
            .where(
                self.model.tenant_id == tenant_id,
                self.model.lote_id == lote_id,
                self.model.deleted_at.is_(None),
            )
            .order_by(self.model.created_at.asc())
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def list_pendientes_para_worker(
        self,
        *,
        tenant_id: UUID,
        limit: int,
        session: AsyncSession,
    ) -> list[Comunicacion]:
        stmt = (
            select(self.model)
            .where(
                self.model.tenant_id == tenant_id,
                self.model.estado == EstadoComunicacion.Pendiente.value,
                self.model.requiere_aprobacion.is_(False),
                self.model.deleted_at.is_(None),
            )
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_estado(
        self,
        *,
        tenant_id: UUID,
        estado: EstadoComunicacion,
        session: AsyncSession,
    ) -> list[Comunicacion]:
        stmt = (
            select(self.model)
            .where(
                self.model.tenant_id == tenant_id,
                self.model.estado == estado.value,
                self.model.deleted_at.is_(None),
            )
            .order_by(self.model.created_at.asc())
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def aprobar_lote(
        self,
        *,
        tenant_id: UUID,
        lote_id: UUID,
        session: AsyncSession,
    ) -> int:
        stmt = (
            update(self.model)
            .where(
                self.model.tenant_id == tenant_id,
                self.model.lote_id == lote_id,
                self.model.estado == EstadoComunicacion.Pendiente.value,
                self.model.deleted_at.is_(None),
            )
            .values(estado=EstadoComunicacion.Enviando.value)
            .returning(self.model.id)
        )
        result = await session.execute(stmt)
        await session.flush()
        return len(result.all())

    async def cancelar_lote(
        self,
        *,
        tenant_id: UUID,
        lote_id: UUID,
        session: AsyncSession,
    ) -> int:
        stmt = (
            update(self.model)
            .where(
                self.model.tenant_id == tenant_id,
                self.model.lote_id == lote_id,
                self.model.estado == EstadoComunicacion.Pendiente.value,
                self.model.deleted_at.is_(None),
            )
            .values(estado=EstadoComunicacion.Cancelado.value)
            .returning(self.model.id)
        )
        result = await session.execute(stmt)
        await session.flush()
        return len(result.all())

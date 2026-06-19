from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.acknowledgment import AcknowledgmentAviso


class AcknowledgmentRepository:
    async def add_or_ignore(
        self,
        *,
        tenant_id: UUID,
        aviso_id: UUID,
        usuario_id: UUID,
        session: AsyncSession,
    ) -> AcknowledgmentAviso:
        stmt = (
            pg_insert(AcknowledgmentAviso)
            .values(
                tenant_id=tenant_id,
                aviso_id=aviso_id,
                usuario_id=usuario_id,
            )
            .on_conflict_do_nothing(
                constraint="uq_ack_aviso_tenant_usuario",
            )
            .returning(AcknowledgmentAviso)
        )
        result = await session.execute(stmt)
        await session.flush()
        row = result.scalar_one_or_none()
        if row is None:
            stmt = select(AcknowledgmentAviso).where(
                AcknowledgmentAviso.tenant_id == tenant_id,
                AcknowledgmentAviso.aviso_id == aviso_id,
                AcknowledgmentAviso.usuario_id == usuario_id,
            )
            result = await session.execute(stmt)
            row = result.scalar_one()
        return row

    async def exists(
        self,
        *,
        tenant_id: UUID,
        aviso_id: UUID,
        usuario_id: UUID,
        session: AsyncSession,
    ) -> bool:
        stmt = select(
            select(AcknowledgmentAviso)
            .where(
                AcknowledgmentAviso.tenant_id == tenant_id,
                AcknowledgmentAviso.aviso_id == aviso_id,
                AcknowledgmentAviso.usuario_id == usuario_id,
            )
            .exists()
        )
        result = await session.execute(stmt)
        return result.scalar() or False

    async def count_by_aviso(
        self,
        *,
        aviso_id: UUID,
        session: AsyncSession,
    ) -> int:
        stmt = select(func.count()).where(
            AcknowledgmentAviso.aviso_id == aviso_id
        )
        result = await session.execute(stmt)
        return result.scalar() or 0

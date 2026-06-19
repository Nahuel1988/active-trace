from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.acknowledgment import AcknowledgmentAviso
from app.models.aviso import Aviso
from app.repositories.base import BaseRepository


class AvisoRepository(BaseRepository[Aviso]):
    def __init__(self) -> None:
        super().__init__(Aviso)

    async def get_by_id(
        self, *, id: UUID, tenant_id: UUID, session: AsyncSession
    ) -> Optional[Aviso]:
        return await self.get(id=id, tenant_id=tenant_id, session=session)

    async def list_all(
        self, *, tenant_id: UUID, session: AsyncSession
    ) -> list[Aviso]:
        stmt = (
            select(Aviso)
            .where(
                Aviso.tenant_id == tenant_id,
                Aviso.deleted_at.is_(None),
            )
            .order_by(Aviso.orden.asc(), Aviso.created_at.desc())
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def list_visibles(
        self,
        *,
        tenant_id: UUID,
        materia_ids: list[UUID],
        cohorte_ids: list[UUID],
        roles: list[str],
        usuario_id: UUID,
        session: AsyncSession,
    ) -> list[Aviso]:
        now = datetime.now(timezone.utc)
        stmt = (
            select(Aviso)
            .where(
                Aviso.tenant_id == tenant_id,
                Aviso.deleted_at.is_(None),
                Aviso.activo.is_(True),
                Aviso.inicio_en <= now,
                Aviso.fin_en >= now,
            )
            .order_by(Aviso.orden.asc(), Aviso.created_at.desc())
        )
        result = await session.execute(stmt)
        avisos = list(result.scalars().all())

        filtered = []
        for aviso in avisos:
            if aviso.alcance == "global":
                filtered.append(aviso)
            elif aviso.alcance == "por_materia" and aviso.materia_id in materia_ids:
                filtered.append(aviso)
            elif aviso.alcance == "por_cohorte" and aviso.cohorte_id in cohorte_ids:
                filtered.append(aviso)
            elif aviso.alcance == "por_rol" and aviso.rol_destino in roles:
                filtered.append(aviso)

        return filtered

    async def count_acks(
        self, *, aviso_id: UUID, session: AsyncSession
    ) -> int:
        stmt = select(func.count()).where(
            AcknowledgmentAviso.aviso_id == aviso_id
        )
        result = await session.execute(stmt)
        return result.scalar() or 0

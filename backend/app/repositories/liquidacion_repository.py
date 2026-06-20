"""LiquidacionRepository — acceso a datos para Liquidacion."""

from __future__ import annotations

import uuid
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.liquidacion import EstadoLiquidacion, Liquidacion
from app.repositories.base import BaseRepository


class LiquidacionRepository(BaseRepository[Liquidacion]):
    """Repositorio para Liquidacion con soporte de upsert batch y cierre."""

    def __init__(self) -> None:
        super().__init__(Liquidacion)

    async def get_by_cohorte_periodo(
        self,
        *,
        tenant_id: UUID,
        cohorte_id: UUID,
        periodo: str,
        session: AsyncSession,
        usuario_id: UUID | None = None,
    ) -> list[Liquidacion]:
        """Retorna liquidaciones activas de una cohorte en un período."""
        stmt = select(self.model).where(
            self.model.tenant_id == tenant_id,
            self.model.cohorte_id == cohorte_id,
            self.model.periodo == periodo,
            self.model.deleted_at.is_(None),
        )
        if usuario_id is not None:
            stmt = stmt.where(self.model.usuario_id == usuario_id)
        stmt = stmt.order_by(self.model.created_at)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def get_cerradas(
        self,
        *,
        tenant_id: UUID,
        session: AsyncSession,
        cohorte_id: UUID | None = None,
        periodo: str | None = None,
        usuario_id: UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Liquidacion]:
        """Lista liquidaciones con estado 'Cerrada', con filtros opcionales."""
        stmt = select(self.model).where(
            self.model.tenant_id == tenant_id,
            self.model.estado == EstadoLiquidacion.Cerrada.value,
            self.model.deleted_at.is_(None),
        )
        if cohorte_id is not None:
            stmt = stmt.where(self.model.cohorte_id == cohorte_id)
        if periodo is not None:
            stmt = stmt.where(self.model.periodo == periodo)
        if usuario_id is not None:
            stmt = stmt.where(self.model.usuario_id == usuario_id)
        stmt = stmt.order_by(self.model.periodo.desc(), self.model.created_at).offset(offset).limit(limit)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def create_or_update_batch(
        self,
        *,
        tenant_id: UUID,
        cohorte_id: UUID,
        periodo: str,
        liquidaciones: list[Liquidacion],
        session: AsyncSession,
    ) -> list[Liquidacion]:
        """Upsert batch: reemplaza liquidaciones Abiertas del período.

        - Soft-deletes todas las Abiertas existentes para (cohorte_id, periodo).
        - Inserta los nuevos registros.
        - Las Cerradas no se tocan.
        """
        # Soft-delete abiertas existentes
        stmt_delete = (
            update(self.model)
            .where(
                self.model.tenant_id == tenant_id,
                self.model.cohorte_id == cohorte_id,
                self.model.periodo == periodo,
                self.model.estado == EstadoLiquidacion.Abierta.value,
                self.model.deleted_at.is_(None),
            )
            .values(deleted_at=func.now())
        )
        await session.execute(stmt_delete)

        # Insertar nuevas
        creadas: list[Liquidacion] = []
        for liq in liquidaciones:
            session.add(liq)
        await session.flush()
        for liq in liquidaciones:
            await session.refresh(liq)
            creadas.append(liq)
        return creadas

    async def cerrar(
        self,
        *,
        tenant_id: UUID,
        liquidacion_id: UUID,
        session: AsyncSession,
    ) -> int:
        """Cambia estado a 'Cerrada' si estaba 'Abierta'.

        Retorna el número de filas afectadas (0 = no encontrada o ya cerrada).
        """
        stmt = (
            update(self.model)
            .where(
                self.model.id == liquidacion_id,
                self.model.tenant_id == tenant_id,
                self.model.estado == EstadoLiquidacion.Abierta.value,
                self.model.deleted_at.is_(None),
            )
            .values(estado=EstadoLiquidacion.Cerrada.value)
            .returning(self.model.id)
        )
        result = await session.execute(stmt)
        await session.flush()
        rows = result.fetchall()
        return len(rows)

    async def exists_cerradas(
        self,
        *,
        tenant_id: UUID,
        cohorte_id: UUID,
        periodo: str,
        session: AsyncSession,
    ) -> bool:
        """Retorna True si existen liquidaciones Cerradas para (cohorte_id, periodo)."""
        stmt = select(self.model.id).where(
            self.model.tenant_id == tenant_id,
            self.model.cohorte_id == cohorte_id,
            self.model.periodo == periodo,
            self.model.estado == EstadoLiquidacion.Cerrada.value,
            self.model.deleted_at.is_(None),
        ).limit(1)
        result = await session.execute(stmt)
        return result.scalar_one_or_none() is not None

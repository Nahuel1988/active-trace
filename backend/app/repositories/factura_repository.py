"""FacturaRepository — acceso a datos para Factura."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.factura import EstadoFactura, Factura
from app.repositories.base import BaseRepository


class FacturaRepository(BaseRepository[Factura]):
    """Repositorio para Factura con métodos de listado y transición de estado."""

    def __init__(self) -> None:
        super().__init__(Factura)

    async def list_filtered(
        self,
        *,
        tenant_id: UUID,
        session: AsyncSession,
        periodo: str | None = None,
        estado: str | None = None,
        usuario_id: UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Factura]:
        """Lista facturas activas con filtros opcionales."""
        stmt = select(self.model).where(
            self.model.tenant_id == tenant_id,
            self.model.deleted_at.is_(None),
        )
        if periodo is not None:
            stmt = stmt.where(self.model.periodo == periodo)
        if estado is not None:
            stmt = stmt.where(self.model.estado == estado)
        if usuario_id is not None:
            stmt = stmt.where(self.model.usuario_id == usuario_id)
        stmt = stmt.order_by(self.model.cargada_at.desc()).offset(offset).limit(limit)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def update_pendiente(
        self,
        *,
        obj: Factura,
        session: AsyncSession,
    ) -> Factura:
        """Actualiza una Factura solo si está en estado Pendiente.

        Retorna el objeto actualizado o lanza ValueError si no está Pendiente.
        """
        if obj.estado != EstadoFactura.Pendiente.value:
            raise ValueError("Solo se puede editar una Factura en estado Pendiente")
        await session.flush()
        await session.refresh(obj)
        return obj

    async def abonar(
        self,
        *,
        tenant_id: UUID,
        factura_id: UUID,
        session: AsyncSession,
    ) -> int:
        """Cambia estado a 'Abonada' y registra abonada_at.

        Retorna filas afectadas (0 = no encontrada o ya Abonada).
        """
        stmt = (
            update(self.model)
            .where(
                self.model.id == factura_id,
                self.model.tenant_id == tenant_id,
                self.model.estado == EstadoFactura.Pendiente.value,
                self.model.deleted_at.is_(None),
            )
            .values(
                estado=EstadoFactura.Abonada.value,
                abonada_at=func.now(),
            )
            .returning(self.model.id)
        )
        result = await session.execute(stmt)
        await session.flush()
        rows = result.fetchall()
        return len(rows)

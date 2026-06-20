"""CalificacionRepository — acceso a datos para Calificacion.

Operaciones: consulta por materia+usuario, bulk insert, soft-delete
por materia+usuario, consulta por entrada de padrón.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.calificacion import Calificacion
from app.repositories.base import BaseRepository


class CalificacionRepository(BaseRepository[Calificacion]):
    """Repositorio para Calificacion."""

    def __init__(self) -> None:
        super().__init__(Calificacion)

    async def get_by_materia_y_usuario(
        self,
        *,
        tenant_id: UUID,
        materia_id: UUID,
        creado_por: UUID,
        session: AsyncSession,
    ) -> list[Calificacion]:
        """Retorna calificaciones de un usuario para una materia.

        Args:
            tenant_id: UUID del tenant.
            materia_id: UUID de la materia.
            creado_por: UUID del usuario que creó las calificaciones.
            session: Sesión async de SQLAlchemy.

        Returns:
            Lista de calificaciones activas (no soft-deleteadas).
        """
        stmt = (
            select(self.model)
            .where(
                self.model.tenant_id == tenant_id,  # type: ignore[attr-defined]
                self.model.materia_id == materia_id,  # type: ignore[attr-defined]
                self.model.creado_por == creado_por,  # type: ignore[attr-defined]
                self.model.deleted_at.is_(None),  # type: ignore[attr-defined]
            )
            .order_by(self.model.created_at.asc())  # type: ignore[attr-defined]
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def bulk_create(
        self,
        *,
        calificaciones: list[Calificacion],
        session: AsyncSession,
    ) -> list[Calificacion]:
        """Inserta múltiples calificaciones en una transacción.

        Args:
            calificaciones: Lista de objetos Calificacion a insertar.
            session: Sesión async.

        Returns:
            Lista de calificaciones insertadas con sus IDs generados.
        """
        if not calificaciones:
            return []
        for c in calificaciones:
            session.add(c)
        await session.flush()
        for c in calificaciones:
            await session.refresh(c)
        return calificaciones

    async def soft_delete_by_materia_y_usuario(
        self,
        *,
        tenant_id: UUID,
        materia_id: UUID,
        creado_por: UUID,
        deleted_by: UUID,
        session: AsyncSession,
    ) -> int:
        """Marca calificaciones como soft-delete para (tenant, materia, creado_por).

        Args:
            tenant_id: UUID del tenant.
            materia_id: UUID de la materia.
            creado_por: UUID del usuario que creó las calificaciones.
            deleted_by: UUID del usuario que realiza el vaciado.
            session: Sesión async.

        Returns:
            Cantidad de registros afectados.
        """
        stmt = (
            update(self.model)
            .where(
                self.model.tenant_id == tenant_id,  # type: ignore[attr-defined]
                self.model.materia_id == materia_id,  # type: ignore[attr-defined]
                self.model.creado_por == creado_por,  # type: ignore[attr-defined]
                self.model.deleted_at.is_(None),  # type: ignore[attr-defined]
            )
            .values(
                deleted_at=func.now(),
                deleted_by=deleted_by,
            )
            .returning(self.model.id)  # type: ignore[attr-defined]
        )
        result = await session.execute(stmt)
        await session.flush()
        return len(result.fetchall())

    async def get_by_entrada_padron(
        self,
        *,
        tenant_id: UUID,
        entrada_padron_id: UUID,
        materia_id: UUID,
        session: AsyncSession,
    ) -> list[Calificacion]:
        """Retorna calificaciones de un alumno para una materia.

        Args:
            tenant_id: UUID del tenant.
            entrada_padron_id: UUID de la entrada de padrón (alumno).
            materia_id: UUID de la materia.
            session: Sesión async.

        Returns:
            Lista de calificaciones activas del alumno en la materia.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.tenant_id == tenant_id,  # type: ignore[attr-defined]
                self.model.entrada_padron_id == entrada_padron_id,  # type: ignore[attr-defined]
                self.model.materia_id == materia_id,  # type: ignore[attr-defined]
                self.model.deleted_at.is_(None),  # type: ignore[attr-defined]
            )
            .order_by(self.model.created_at.asc())  # type: ignore[attr-defined]
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

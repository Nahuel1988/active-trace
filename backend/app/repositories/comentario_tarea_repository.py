"""ComentarioTareaRepository — acceso a comentarios de tareas.

Append-only: no hay update ni delete.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.comentario_tarea import ComentarioTarea
from app.repositories.base import BaseRepository


class ComentarioTareaRepository(BaseRepository[ComentarioTarea]):
    """Repositorio para ComentarioTarea (append-only, solo lectura/creación)."""

    def __init__(self) -> None:
        super().__init__(ComentarioTarea)

    async def list_by_tarea(
        self,
        *,
        tenant_id: UUID,
        tarea_id: UUID,
        session: AsyncSession,
    ) -> list[ComentarioTarea]:
        """Lista comentarios de una tarea en orden cronológico ascendente.

        Args:
            tenant_id: UUID del tenant (filtro de seguridad multi-tenant).
            tarea_id: UUID de la tarea.
            session: Sesión async de SQLAlchemy.

        Returns:
            Lista de ``ComentarioTarea`` ordenada por ``creado_at`` ASC.
        """
        stmt = (
            select(self.model)
            .where(
                self.model.tenant_id == tenant_id,  # type: ignore[attr-defined]
                self.model.tarea_id == tarea_id,     # type: ignore[attr-defined]
            )
            .order_by(self.model.creado_at.asc())  # type: ignore[attr-defined]
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

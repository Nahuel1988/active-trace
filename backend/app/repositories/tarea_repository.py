"""TareaRepository — operaciones de acceso a datos para Tarea."""

from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tarea import EstadoTarea, Tarea
from app.repositories.base import BaseRepository


class TareaRepository(BaseRepository[Tarea]):
    """Repositorio para Tarea con filtros dinámicos y scope por rol."""

    def __init__(self) -> None:
        super().__init__(Tarea)

    async def list_filtered(
        self,
        *,
        tenant_id: UUID,
        session: AsyncSession,
        asignado_a: UUID | None = None,
        asignado_por: UUID | None = None,
        materia_id: UUID | None = None,
        estado: EstadoTarea | None = None,
        q: str | None = None,
        scope_user_id: UUID | None = None,
    ) -> list[Tarea]:
        """Lista tareas con filtros opcionales y always-on tenant + soft-delete.

        Args:
            tenant_id: UUID del tenant (siempre aplicado).
            session: Sesión async de SQLAlchemy.
            asignado_a: Filtrar por usuario asignado.
            asignado_por: Filtrar por usuario asignador.
            materia_id: Filtrar por materia.
            estado: Filtrar por estado.
            q: Búsqueda ILIKE sobre descripcion.
            scope_user_id: Si se pasa, restringe a tareas donde el usuario
                es ``asignado_a`` o ``asignado_por`` (alcance PROFESOR).
        """
        stmt = select(self.model).where(
            self.model.tenant_id == tenant_id,  # type: ignore[attr-defined]
            self.model.deleted_at.is_(None),     # type: ignore[attr-defined]
        )

        if asignado_a is not None:
            stmt = stmt.where(self.model.asignado_a == asignado_a)  # type: ignore[attr-defined]
        if asignado_por is not None:
            stmt = stmt.where(self.model.asignado_por == asignado_por)  # type: ignore[attr-defined]
        if materia_id is not None:
            stmt = stmt.where(self.model.materia_id == materia_id)  # type: ignore[attr-defined]
        if estado is not None:
            stmt = stmt.where(self.model.estado == estado.value)  # type: ignore[attr-defined]
        if q is not None and q.strip():
            stmt = stmt.where(
                self.model.descripcion.ilike(f"%{q}%")  # type: ignore[attr-defined]
            )
        if scope_user_id is not None:
            stmt = stmt.where(
                or_(
                    self.model.asignado_a == scope_user_id,   # type: ignore[attr-defined]
                    self.model.asignado_por == scope_user_id,  # type: ignore[attr-defined]
                )
            )

        stmt = stmt.order_by(self.model.created_at.desc())  # type: ignore[attr-defined]
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def list_mias(
        self,
        *,
        tenant_id: UUID,
        usuario_id: UUID,
        session: AsyncSession,
    ) -> list[Tarea]:
        """Retorna tareas donde el usuario es ``asignado_a`` (mis tareas)."""
        stmt = (
            select(self.model)
            .where(
                self.model.tenant_id == tenant_id,     # type: ignore[attr-defined]
                self.model.asignado_a == usuario_id,    # type: ignore[attr-defined]
                self.model.deleted_at.is_(None),         # type: ignore[attr-defined]
            )
            .order_by(self.model.created_at.desc())  # type: ignore[attr-defined]
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

"""AuditLogRepository — solo add y list, sin métodos de mutación.

El registro de auditoría es append-only. Este repositorio:
- Hereda de ``BaseRepository[AuditLog]`` para acceso a la sesión y typing.
- Expone únicamente ``add`` (escritura) y ``list`` (lectura tenant-scoped).
- NO expone ``update``, ``delete``, ``soft_delete`` ni ninguna operación de
  modificación. La inmutabilidad se refuerza a nivel DB (reglas PostgreSQL).
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.repositories.base import BaseRepository


class AuditLogRepository(BaseRepository[AuditLog]):
    """Repositorio append-only para el registro de auditoría.

    Solo permite:
    - ``add``: persistir una nueva entrada.
    - ``list``: leer entradas por tenant (scope obligatorio).

    Los métodos heredados ``update`` y ``soft_delete`` lanzan
    ``NotImplementedError`` porque la auditoría es inmutable.
    """

    def __init__(self) -> None:
        super().__init__(AuditLog)

    async def create(self, *args: object, **kwargs: object) -> object:  # type: ignore[explicit-any]
        msg = "AuditLogRepository does not support create — use add() instead (append-only)"
        raise NotImplementedError(msg)

    def update(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        msg = "AuditLogRepository does not support update (append-only)"
        raise NotImplementedError(msg)

    def soft_delete(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        msg = "AuditLogRepository does not support delete (append-only)"
        raise NotImplementedError(msg)

    async def add(
        self,
        *,
        entry: AuditLog,
        session: AsyncSession,
    ) -> AuditLog:
        """Persiste una nueva entrada de auditoría.

        Args:
            entry: Instancia de ``AuditLog`` (sin persistir).
            session: Sesión async de SQLAlchemy.

        Returns:
            La misma entrada con ``id`` y ``fecha_hora`` generados.
        """
        session.add(entry)
        await session.flush()
        await session.refresh(entry)
        return entry

    async def list(
        self,
        *,
        tenant_id: UUID,
        session: AsyncSession,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AuditLog]:
        """Retorna entradas de auditoría para un tenant, ordenadas por fecha.

        Args:
            tenant_id: UUID del tenant (scope obligatorio).
            session: Sesión async de SQLAlchemy.
            limit: Máximo de registros a retornar (default 50).
            offset: Desplazamiento para paginación (default 0).

        Returns:
            Lista de ``AuditLog`` del tenant, más recientes primero.
        """
        stmt = (
            select(self.model)
            .where(self.model.tenant_id == tenant_id)  # type: ignore[attr-defined]
            .order_by(self.model.fecha_hora.desc())     # type: ignore[attr-defined]
            .offset(offset)
            .limit(limit)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

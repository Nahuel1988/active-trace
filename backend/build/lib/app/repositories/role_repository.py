"""RoleRepository — operaciones de acceso a datos para el modelo Role.

Métodos específicos:
    get_by_code: búsqueda por code con tenant-scope.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.role import Role
from app.repositories.base import BaseRepository


class RoleRepository(BaseRepository[Role]):
    """Repositorio para el modelo Role con tenant-scoping."""

    def __init__(self) -> None:
        super().__init__(Role)

    async def get_by_code(
        self,
        *,
        tenant_id: UUID,
        code: str,
        session: AsyncSession,
    ) -> Role | None:
        """Busca un rol por code dentro de un tenant.

        Args:
            tenant_id: UUID del tenant.
            code: Código interno del rol (ej: ``admin``, ``profesor``).
            session: Sesión de base de datos async.

        Returns:
            Role si existe y no está soft-deleteado, None en caso contrario.
        """
        stmt = select(self.model).where(
            self.model.code == code,          # type: ignore[attr-defined]
            self.model.tenant_id == tenant_id,  # type: ignore[attr-defined]
            self.model.deleted_at.is_(None),    # type: ignore[attr-defined]
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

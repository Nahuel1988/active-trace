"""UserRepository — operaciones de acceso a datos para User.

Métodos específicos:
    get_by_email_lookup: búsqueda por email_lookup con tenant-scope.
    get_active_by_email_lookup: igual pero filtrando is_active=True.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repositorio para el modelo User con tenant-scoping."""

    def __init__(self) -> None:
        super().__init__(User)

    async def get_by_email_lookup(
        self,
        *,
        tenant_id: UUID,
        email_lookup: str,
        session: AsyncSession,
    ) -> User | None:
        """Busca un usuario por email_lookup dentro de un tenant.

        Args:
            tenant_id: UUID del tenant.
            email_lookup: Hash HMAC del email (ya calculado).
            session: Sesión de base de datos async.

        Returns:
            User si existe y no está soft-deleteado, None en caso contrario.
        """
        stmt = select(self.model).where(
            self.model.email_lookup == email_lookup,  # type: ignore[attr-defined]
            self.model.tenant_id == tenant_id,          # type: ignore[attr-defined]
            self.model.deleted_at.is_(None),             # type: ignore[attr-defined]
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_by_email_lookup(
        self,
        *,
        tenant_id: UUID,
        email_lookup: str,
        session: AsyncSession,
    ) -> User | None:
        """Busca un usuario activo por email_lookup dentro de un tenant.

        Además de los filtros de get_by_email_lookup, exige is_active=True.
        """
        stmt = select(self.model).where(
            self.model.email_lookup == email_lookup,  # type: ignore[attr-defined]
            self.model.tenant_id == tenant_id,          # type: ignore[attr-defined]
            self.model.is_active.is_(True),              # type: ignore[attr-defined]
            self.model.deleted_at.is_(None),             # type: ignore[attr-defined]
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

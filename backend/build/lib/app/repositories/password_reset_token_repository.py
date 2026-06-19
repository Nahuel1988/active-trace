"""PasswordResetTokenRepository — operaciones de acceso a datos para
PasswordResetToken.

Métodos específicos:
    get_by_hash: búsqueda por hash del token con tenant-scope.
    mark_used: marca used_at = now().
"""

from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.password_reset_token import PasswordResetToken
from app.repositories.base import BaseRepository


class PasswordResetTokenRepository(BaseRepository[PasswordResetToken]):
    """Repositorio para el modelo PasswordResetToken con tenant-scoping."""

    def __init__(self) -> None:
        super().__init__(PasswordResetToken)

    async def get_by_hash(
        self,
        *,
        token_hash: str,
        tenant_id: UUID,
        session: AsyncSession,
    ) -> PasswordResetToken | None:
        """Busca un token de reseteo por su hash dentro de un tenant.

        Args:
            token_hash: SHA-256 del token.
            tenant_id: UUID del tenant.
            session: Sesión de base de datos async.

        Returns:
            PasswordResetToken si existe y no está soft-deleteado,
            None en caso contrario.
        """
        stmt = select(self.model).where(
            self.model.token_hash == token_hash,  # type: ignore[attr-defined]
            self.model.tenant_id == tenant_id,      # type: ignore[attr-defined]
            self.model.deleted_at.is_(None),         # type: ignore[attr-defined]
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def mark_used(
        self,
        *,
        id: UUID,
        tenant_id: UUID,
        session: AsyncSession,
    ) -> bool:
        """Marca un token de reseteo como usado.

        Setea ``used_at = now()`` en el token identificado por ``id``
        dentro del tenant especificado.

        Args:
            id: UUID del token a marcar.
            tenant_id: UUID del tenant.
            session: Sesión de base de datos async.

        Returns:
            True si se actualizó algún registro, False si no se encontró.
        """
        stmt = (
            update(self.model)
            .where(
                self.model.id == id,                # type: ignore[attr-defined]
                self.model.tenant_id == tenant_id,   # type: ignore[attr-defined]
            )
            .values(used_at=func.now())
            .returning(self.model.id)                # type: ignore[attr-defined]
        )
        result = await session.execute(stmt)
        await session.flush()
        return result.scalar_one_or_none() is not None

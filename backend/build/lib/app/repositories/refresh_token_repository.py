"""RefreshTokenRepository — operaciones de acceso a datos para RefreshToken.

Métodos específicos:
    get_by_hash: búsqueda por hash del token con tenant-scope.
    revoke: revoca un token individual (setea revoked_at).
    revoke_family: revoca todos los tokens de una familia (replay detection).
"""

from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.refresh_token import RefreshToken
from app.repositories.base import BaseRepository


class RefreshTokenRepository(BaseRepository[RefreshToken]):
    """Repositorio para el modelo RefreshToken con tenant-scoping."""

    def __init__(self) -> None:
        super().__init__(RefreshToken)

    async def get_by_hash(
        self,
        *,
        token_hash: str,
        tenant_id: UUID,
        session: AsyncSession,
    ) -> RefreshToken | None:
        """Busca un token por su hash dentro de un tenant.

        Args:
            token_hash: SHA-256 del token.
            tenant_id: UUID del tenant.
            session: Sesión de base de datos async.

        Returns:
            RefreshToken si existe y no está soft-deleteado, None en caso contrario.
        """
        stmt = select(self.model).where(
            self.model.token_hash == token_hash,  # type: ignore[attr-defined]
            self.model.tenant_id == tenant_id,      # type: ignore[attr-defined]
            self.model.deleted_at.is_(None),         # type: ignore[attr-defined]
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def revoke(
        self,
        *,
        id: UUID,
        tenant_id: UUID,
        session: AsyncSession,
    ) -> bool:
        """Revoca un token refresh individual.

        Setea ``revoked_at = now()`` en el token identificado por ``id``
        dentro del tenant especificado.

        Args:
            id: UUID del token a revocar.
            tenant_id: UUID del tenant.
            session: Sesión de base de datos async.

        Returns:
            True si se revocó algún registro, False si no se encontró.
        """
        stmt = (
            update(self.model)
            .where(
                self.model.id == id,                # type: ignore[attr-defined]
                self.model.tenant_id == tenant_id,   # type: ignore[attr-defined]
            )
            .values(revoked_at=func.now())
            .returning(self.model.id)                # type: ignore[attr-defined]
        )
        result = await session.execute(stmt)
        await session.flush()
        return result.scalar_one_or_none() is not None

    async def revoke_family(
        self,
        *,
        family_id: UUID,
        tenant_id: UUID,
        session: AsyncSession,
    ) -> int:
        """Revoca todos los tokens activos de una familia.

        Útil para detección de re-use: si un token ya usado se intenta
        reutilizar, se revoca toda la familia.

        Args:
            family_id: UUID de la familia de tokens.
            tenant_id: UUID del tenant.
            session: Sesión de base de datos async.

        Returns:
            Cantidad de tokens revocados.
        """
        stmt = (
            update(self.model)
            .where(
                self.model.family_id == family_id,    # type: ignore[attr-defined]
                self.model.tenant_id == tenant_id,      # type: ignore[attr-defined]
                self.model.revoked_at.is_(None),         # type: ignore[attr-defined]
                self.model.deleted_at.is_(None),         # type: ignore[attr-defined]
            )
            .values(revoked_at=func.now())
            .returning(self.model.id)                    # type: ignore[attr-defined]
        )
        result = await session.execute(stmt)
        await session.flush()
        rows = result.all()
        return len(rows)

    async def revoke_all_for_user(
        self,
        *,
        user_id: UUID,
        tenant_id: UUID,
        session: AsyncSession,
    ) -> int:
        """Revoca todos los tokens refresh activos de un usuario.

        Args:
            user_id: UUID del usuario.
            tenant_id: UUID del tenant.
            session: Sesión de base de datos async.

        Returns:
            Cantidad de tokens revocados.
        """
        stmt = (
            update(self.model)
            .where(
                self.model.user_id == user_id,           # type: ignore[attr-defined]
                self.model.tenant_id == tenant_id,        # type: ignore[attr-defined]
                self.model.revoked_at.is_(None),           # type: ignore[attr-defined]
                self.model.deleted_at.is_(None),           # type: ignore[attr-defined]
            )
            .values(revoked_at=func.now())
            .returning(self.model.id)                      # type: ignore[attr-defined]
        )
        result = await session.execute(stmt)
        await session.flush()
        rows = result.all()
        return len(rows)

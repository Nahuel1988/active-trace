"""TotpSecretRepository — operaciones de acceso a datos para TotpSecret.

Métodos específicos:
    get_by_user: obtiene el secreto TOTP de un usuario.
    upsert: crea o actualiza el secreto TOTP.
    confirm: marca confirmed_at = now().
"""

from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.totp_secret import TotpSecret
from app.repositories.base import BaseRepository


class TotpSecretRepository(BaseRepository[TotpSecret]):
    """Repositorio para el modelo TotpSecret con tenant-scoping."""

    def __init__(self) -> None:
        super().__init__(TotpSecret)

    async def get_by_user(
        self,
        *,
        user_id: UUID,
        tenant_id: UUID,
        session: AsyncSession,
    ) -> TotpSecret | None:
        """Obtiene el secreto TOTP de un usuario dentro de un tenant.

        Args:
            user_id: UUID del usuario.
            tenant_id: UUID del tenant.
            session: Sesión de base de datos async.

        Returns:
            TotpSecret si existe, None en caso contrario.
        """
        stmt = select(self.model).where(
            self.model.user_id == user_id,          # type: ignore[attr-defined]
            self.model.tenant_id == tenant_id,       # type: ignore[attr-defined]
            self.model.deleted_at.is_(None),          # type: ignore[attr-defined]
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert(
        self,
        *,
        user_id: UUID,
        tenant_id: UUID,
        secret_encrypted: str,
        session: AsyncSession,
    ) -> TotpSecret:
        """Crea o actualiza el secreto TOTP de un usuario.

        Si ya existe un secreto para el usuario dentro del tenant, lo
        actualiza y resetea ``confirmed_at``. Si no existe, lo crea.

        Args:
            user_id: UUID del usuario.
            tenant_id: UUID del tenant.
            secret_encrypted: Secreto TOTP cifrado.
            session: Sesión de base de datos async.

        Returns:
            TotpSecret creado o actualizado.
        """
        existing = await self.get_by_user(
            user_id=user_id,
            tenant_id=tenant_id,
            session=session,
        )
        if existing is not None:
            existing.secret_encrypted = secret_encrypted
            existing.confirmed_at = None
            await session.flush()
            await session.refresh(existing)
            return existing

        obj = self.model(
            user_id=user_id,
            tenant_id=tenant_id,
            secret_encrypted=secret_encrypted,
        )
        session.add(obj)
        await session.flush()
        await session.refresh(obj)
        return obj

    async def confirm(
        self,
        *,
        user_id: UUID,
        tenant_id: UUID,
        session: AsyncSession,
    ) -> bool:
        """Marca el secreto TOTP de un usuario como confirmado.

        Setea ``confirmed_at = now()`` para el secreto del usuario
        dentro del tenant especificado.

        Args:
            user_id: UUID del usuario.
            tenant_id: UUID del tenant.
            session: Sesión de base de datos async.

        Returns:
            True si se actualizó algún registro, False si no se encontró.
        """
        stmt = (
            update(self.model)
            .where(
                self.model.user_id == user_id,        # type: ignore[attr-defined]
                self.model.tenant_id == tenant_id,     # type: ignore[attr-defined]
                self.model.deleted_at.is_(None),        # type: ignore[attr-defined]
            )
            .values(confirmed_at=func.now())
            .returning(self.model.id)                   # type: ignore[attr-defined]
        )
        result = await session.execute(stmt)
        await session.flush()
        return result.scalar_one_or_none() is not None

"""PermisoRepository — operaciones de acceso a datos para el modelo Permiso.

Métodos específicos:
    get_by_code: búsqueda por code con tenant-scope.
    get_effective_permissions: resolución de permisos efectivos por request.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.permiso import Permiso
from app.repositories.base import BaseRepository


class PermisoRepository(BaseRepository[Permiso]):
    """Repositorio para el modelo Permiso con tenant-scoping."""

    def __init__(self) -> None:
        super().__init__(Permiso)

    async def get_by_code(
        self,
        *,
        tenant_id: UUID,
        code: str,
        session: AsyncSession,
    ) -> Permiso | None:
        """Busca un permiso por code dentro de un tenant.

        Args:
            tenant_id: UUID del tenant.
            code: Código del permiso (ej: ``comunicacion:aprobar``).
            session: Sesión de base de datos async.

        Returns:
            Permiso si existe y no está soft-deleteado, None en caso contrario.
        """
        stmt = select(self.model).where(
            self.model.code == code,          # type: ignore[attr-defined]
            self.model.tenant_id == tenant_id,  # type: ignore[attr-defined]
            self.model.deleted_at.is_(None),    # type: ignore[attr-defined]
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_effective_permissions(
        self,
        *,
        user_id: UUID,
        tenant_id: UUID,
        session: AsyncSession,
    ) -> dict[str, str]:
        """Resuelve los permisos efectivos de un usuario.

        Retorna un dict ``{code: scope_efectivo}`` donde cada entrada es
        la **unión** de permisos de todos los roles vigentes del usuario,
        acotado por tenant y con resolución de conflicto de scope
        (global > propio).

        Args:
            user_id: UUID del usuario.
            tenant_id: UUID del tenant (sesión autenticada).
            session: Sesión de base de datos async.

        Returns:
            Dict ``{code: scope}`` con los permisos efectivos. Vacío si
            el usuario no tiene roles vigentes.
        """
        from sqlalchemy import func as sa_func

        from app.models.permiso import Permiso, RolPermiso
        from app.models.role import UserRole

        now = sa_func.now()

        stmt = (
            select(
                Permiso.code,
                sa_func.min(RolPermiso.scope).label("scope"),
            )
            .select_from(UserRole)
            .join(
                RolPermiso,
                (RolPermiso.role_id == UserRole.role_id)
                & (RolPermiso.tenant_id == UserRole.tenant_id),
            )
            .join(
                Permiso,
                (Permiso.id == RolPermiso.permiso_id)
                & (Permiso.tenant_id == RolPermiso.tenant_id),
            )
            .where(
                UserRole.user_id == user_id,
                UserRole.tenant_id == tenant_id,
                UserRole.desde <= now,
                (UserRole.hasta.is_(None)) | (UserRole.hasta > now),
                Permiso.deleted_at.is_(None),        # type: ignore[attr-defined]
            )
            .group_by(Permiso.code)
        )

        result = await session.execute(stmt)
        rows = result.fetchall()

        # Resolver scope: min('global', 'propio') = 'global' en orden ASCII
        # 'global' < 'propio' → min devuelve 'global' si está presente.
        # Si solo hay 'propio' → min devuelve 'propio'.
        return {row.code: row.scope for row in rows}

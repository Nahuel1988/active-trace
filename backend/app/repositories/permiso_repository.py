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

        C-07 (D5): La resolución consulta DOS fuentes y aplica UNION:
        1. `user_role` — roles globales del tenant (ADMIN, FINANZAS).
        2. `asignacion` — roles con contexto académico vigentes
           (PROFESOR, TUTOR, COORDINADOR, NEXO).

        Retorna un dict ``{code: scope_efectivo}`` donde cada entrada es
        la **unión** de permisos de todos los roles vigentes del usuario,
        acotado por tenant y con resolución de conflicto de scope
        (global > propio, usando min() en ASCII: 'global' < 'propio').

        Args:
            user_id: UUID del usuario.
            tenant_id: UUID del tenant (sesión autenticada).
            session: Sesión de base de datos async.

        Returns:
            Dict ``{code: scope}`` con los permisos efectivos. Vacío si
            el usuario no tiene roles vigentes en ninguna de las dos fuentes.
        """
        from sqlalchemy import func as sa_func, union_all, literal_column

        from app.models.permiso import Permiso, RolPermiso
        from app.models.role import UserRole
        from app.models.asignacion import Asignacion

        now = sa_func.now()

        # ------------------------------------------------------------------
        # Fuente 1: UserRole (roles globales del tenant — C-03)
        # Vigencia: desde <= now AND (hasta IS NULL OR hasta > now)
        # ------------------------------------------------------------------
        stmt_user_role = (
            select(
                Permiso.code.label("code"),
                RolPermiso.scope.label("scope"),
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
        )

        # ------------------------------------------------------------------
        # Fuente 2: Asignacion (roles con contexto académico — C-07)
        # Vigencia: desde <= now AND (hasta IS NULL OR hasta >= now)
        #           AND deleted_at IS NULL
        # ------------------------------------------------------------------
        stmt_asignacion = (
            select(
                Permiso.code.label("code"),
                RolPermiso.scope.label("scope"),
            )
            .select_from(Asignacion)
            .join(
                RolPermiso,
                (RolPermiso.role_id == Asignacion.role_id)
                & (RolPermiso.tenant_id == Asignacion.tenant_id),
            )
            .join(
                Permiso,
                (Permiso.id == RolPermiso.permiso_id)
                & (Permiso.tenant_id == RolPermiso.tenant_id),
            )
            .where(
                Asignacion.usuario_id == user_id,
                Asignacion.tenant_id == tenant_id,
                Asignacion.desde <= now,
                (Asignacion.hasta.is_(None)) | (Asignacion.hasta >= now),
                Asignacion.deleted_at.is_(None),    # type: ignore[attr-defined]
                Permiso.deleted_at.is_(None),        # type: ignore[attr-defined]
            )
        )

        # ------------------------------------------------------------------
        # UNION de ambas fuentes + agrupar por code con min(scope)
        # min('global', 'propio') = 'global' (ASCII order)
        # ------------------------------------------------------------------
        combined = union_all(stmt_user_role, stmt_asignacion).subquery()

        stmt = (
            select(
                combined.c.code,
                sa_func.min(combined.c.scope).label("scope"),
            )
            .group_by(combined.c.code)
        )

        result = await session.execute(stmt)
        rows = result.fetchall()

        return {row.code: row.scope for row in rows}

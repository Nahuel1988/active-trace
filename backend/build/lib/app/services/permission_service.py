"""PermissionService — resolución de permisos efectivos y verificación de scope.

Uso::

    from app.services.permission_service import PermissionService

    service = PermissionService()
    permissions = await service.get_effective_permissions(
        user_id=user.id, tenant_id=user.tenant_id, session=db
    )
    # → {"calificaciones:importar": "propio", ...}

    # Verificar ownership cuando el scope es "propio"
    allowed = PermissionService.is_allowed(
        grant=PermissionGrant(code="calificaciones:importar", scope="propio"),
        owner_id=recurso.profesor_id,
        current_user_id=current_user.id,
    )
"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import PermissionGrant
from app.repositories.permiso_repository import PermisoRepository


class PermissionService:
    """Servicio de resolución de permisos efectivos y verificación de scope.

    Dependencias:
        - PermisoRepository: consulta de permisos y resolución efectiva.
    """

    def __init__(
        self,
        permiso_repo: PermisoRepository | None = None,
    ) -> None:
        self._permiso_repo = permiso_repo or PermisoRepository()

    async def get_effective_permissions(
        self,
        *,
        user_id: UUID,
        tenant_id: UUID,
        session: AsyncSession,
    ) -> dict[str, str]:
        """Retorna los permisos efectivos de un usuario.

        Args:
            user_id: UUID del usuario.
            tenant_id: UUID del tenant (sesión).
            session: Sesión de base de datos async.

        Returns:
            Dict ``{code: scope}``. Vacío si el usuario no tiene roles vigentes.
        """
        return await self._permiso_repo.get_effective_permissions(
            user_id=user_id,
            tenant_id=tenant_id,
            session=session,
        )

    async def verify_permission(
        self,
        *,
        user_id: UUID,
        tenant_id: UUID,
        required_code: str,
        session: AsyncSession,
    ) -> PermissionGrant | None:
        """Verifica si un usuario tiene un permiso específico.

        Args:
            user_id: UUID del usuario.
            tenant_id: UUID del tenant.
            required_code: Código del permiso requerido (``modulo:accion``).
            session: Sesión de base de datos async.

        Returns:
            ``PermissionGrant`` si el usuario posee el permiso,
            ``None`` en caso contrario.
        """
        effective = await self.get_effective_permissions(
            user_id=user_id,
            tenant_id=tenant_id,
            session=session,
        )
        scope = effective.get(required_code)
        if scope is None:
            return None
        return PermissionGrant(code=required_code, scope=scope)

    @staticmethod
    def is_allowed(
        grant: PermissionGrant,
        *,
        owner_id: UUID,
        current_user_id: UUID,
    ) -> bool:
        """Verifica si un ``PermissionGrant`` permite operar sobre un recurso.

        Con ``scope="global"`` concede siempre.
        Con ``scope="propio"`` concede solo si ``owner_id == current_user_id``.

        Args:
            grant: El permiso concedido por ``verify_permission``.
            owner_id: UUID del dueño del recurso.
            current_user_id: UUID del usuario de la sesión.

        Returns:
            ``True`` si la operación está permitida.
        """
        if grant.scope == "global":
            return True
        # scope == "propio"
        return owner_id == current_user_id

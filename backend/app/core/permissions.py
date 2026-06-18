"""Guard ``require_permission`` y tipos compartidos de autorización.

Tipos:
    Scope: ``"global"`` | ``"propio"``.
    PermissionGrant: concesión de permiso (code + scope).

Guard:
    require_permission(code): dependency factory de FastAPI que verifica
    que el usuario autenticado posea el permiso requerido. Fail-closed:
    sin permiso explícito → 403 Forbidden.

Uso en un endpoint::

    from app.core.permissions import require_permission

    @router.get("/comunicaciones")
    async def listar_comunicaciones(
        grant: PermissionGrant = Depends(require_permission("comunicacion:ver")),
    ):
        if grant.scope == "propio":
            # filtrar solo comunicaciones propias
            ...
"""

from collections.abc import Callable
from dataclasses import dataclass
from uuid import UUID

from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db


@dataclass(frozen=True)
class PermissionGrant:
    """Concesión de un permiso a un usuario autenticado.

    Attributes:
        code: Código del permiso (``modulo:accion``).
        scope: Alcance efectivo — ``"global"`` o ``"propio"``.
    """

    code: str
    scope: str


def require_permission(
    required_code: str,
) -> Callable:
    """Dependency factory: exige un permiso específico para acceder al endpoint.

    La dependency:
    1. Resuelve la identidad del usuario desde el JWT (``get_current_user``).
    2. Consulta los permisos efectivos server-side contra la base de datos.
    3. Si el permiso NO está presente → ``HTTPException(403)``.
    4. Si está presente → inyecta un ``PermissionGrant`` con el scope efectivo.

    Args:
        required_code: Código del permiso requerido (ej: ``"comunicacion:aprobar"``).

    Returns:
        Una dependency de FastAPI que retorna ``PermissionGrant``.

    Raises:
        HTTPException 401: si el token no es válido (por ``get_current_user``).
        HTTPException 403: si el usuario no posee el permiso (fail-closed).
    """

    async def _dependency(
        db: AsyncSession = Depends(get_db),
        current_user=Depends(get_current_user),
    ) -> PermissionGrant:
        from app.services.permission_service import PermissionService

        service = PermissionService()
        grant = await service.verify_permission(
            user_id=current_user.id,
            tenant_id=current_user.tenant_id,
            required_code=required_code,
            session=db,
        )

        if grant is None:
            raise HTTPException(
                status_code=403,
                detail="Forbidden: you do not have the required permission",
            )

        return grant

    return _dependency

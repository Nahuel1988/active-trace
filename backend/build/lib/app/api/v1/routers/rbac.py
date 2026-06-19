"""RBAC administration router — catálogo de permisos y matriz rol × permiso.

Endpoints:
    - ``GET /api/v1/rbac/permisos`` — listar catálogo de permisos
    - ``POST /api/v1/rbac/permisos`` — crear un nuevo permiso
    - ``GET /api/v1/rbac/roles`` — listar roles del tenant
    - ``POST /api/v1/rbac/matriz`` — asignar permiso a un rol
    - ``DELETE /api/v1/rbac/matriz`` — quitar permiso de un rol
    - ``GET /api/v1/rbac/matriz`` — listar matriz completa

Todos los endpoints exigen ``require_permission("usuarios:gestionar")``.
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.core.permissions import PermissionGrant, require_permission
from app.models.user import User
from app.schemas.rbac import (
    MatrizRow,
    PermisoCreate,
    PermisoResponse,
    RoleResponse,
    RolPermisoAsignar as PermisoAsignar,
)
from app.services.rbac_admin_service import RbacAdminService, RbacError

logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/api/v1/rbac",
    tags=["rbac"],
)


def _get_admin_service() -> RbacAdminService:
    """Factory para inyectar RbacAdminService."""
    return RbacAdminService()


# ---------------------------------------------------------------------------
# Permisos
# ---------------------------------------------------------------------------


@router.get("/permisos", response_model=list[PermisoResponse])
async def listar_permisos(
    grant: PermissionGrant = Depends(require_permission("usuarios:gestionar")),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: RbacAdminService = Depends(_get_admin_service),
):
    """Lista el catálogo de permisos del tenant."""
    permisos = await service.listar_permisos(
        tenant_id=current_user.tenant_id,
        session=db,
    )
    return [
        PermisoResponse(
            id=str(p.id),
            modulo=p.modulo,
            accion=p.accion,
            code=p.code,
            created_at=p.created_at,
            updated_at=p.updated_at,
        )
        for p in permisos
    ]


@router.post("/permisos", response_model=PermisoResponse, status_code=201)
async def crear_permiso(
    body: PermisoCreate,
    grant: PermissionGrant = Depends(require_permission("usuarios:gestionar")),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: RbacAdminService = Depends(_get_admin_service),
):
    """Crea un nuevo permiso en el catálogo del tenant."""
    try:
        permiso = await service.crear_permiso(
            tenant_id=current_user.tenant_id,
            modulo=body.modulo,
            accion=body.accion,
            session=db,
            asignado_por=current_user.id,
        )
    except RbacError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    return PermisoResponse(
        id=str(permiso.id),
        modulo=permiso.modulo,
        accion=permiso.accion,
        code=permiso.code,
        created_at=permiso.created_at,
        updated_at=permiso.updated_at,
    )


# ---------------------------------------------------------------------------
# Roles
# ---------------------------------------------------------------------------


@router.get("/roles", response_model=list[RoleResponse])
async def listar_roles(
    grant: PermissionGrant = Depends(require_permission("usuarios:gestionar")),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: RbacAdminService = Depends(_get_admin_service),
):
    """Lista los roles del tenant."""
    roles = await service.listar_roles(
        tenant_id=current_user.tenant_id,
        session=db,
    )
    return [
        RoleResponse(
            id=str(r.id),
            code=r.code,
            nombre=r.nombre,
            created_at=r.created_at,
        )
        for r in roles
    ]


# ---------------------------------------------------------------------------
# Matriz rol × permiso
# ---------------------------------------------------------------------------


@router.get("/matriz", response_model=list[MatrizRow])
async def listar_matriz(
    grant: PermissionGrant = Depends(require_permission("usuarios:gestionar")),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: RbacAdminService = Depends(_get_admin_service),
):
    """Lista la matriz completa rol × permiso del tenant."""
    return await service.listar_matriz(
        tenant_id=current_user.tenant_id,
        session=db,
    )


@router.post("/matriz", status_code=201)
async def asignar_permiso_a_rol(
    body: PermisoAsignar,
    grant: PermissionGrant = Depends(require_permission("usuarios:gestionar")),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: RbacAdminService = Depends(_get_admin_service),
):
    """Asigna un permiso a un rol."""
    try:
        await service.asignar_permiso_a_rol(
            tenant_id=current_user.tenant_id,
            role_code=body.role_code,
            permiso_code=body.permiso_code,
            scope=body.scope,
            session=db,
            asignado_por=current_user.id,
        )
    except RbacError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    return {"message": f"Permiso '{body.permiso_code}' asignado a rol '{body.role_code}'"}


@router.delete("/matriz")
async def quitar_permiso_a_rol(
    body: PermisoAsignar,
    grant: PermissionGrant = Depends(require_permission("usuarios:gestionar")),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: RbacAdminService = Depends(_get_admin_service),
):
    """Quita un permiso de un rol (elimina la fila de la matriz)."""
    removed = await service.quitar_permiso_a_rol(
        tenant_id=current_user.tenant_id,
        role_code=body.role_code,
        permiso_code=body.permiso_code,
        session=db,
    )
    if not removed:
        raise HTTPException(
            status_code=404,
            detail=f"Asignación '{body.role_code}' + '{body.permiso_code}' no encontrada",
        )
    return {"message": f"Permiso '{body.permiso_code}' quitado de rol '{body.role_code}'"}

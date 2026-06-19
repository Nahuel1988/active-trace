"""Impersonation router — inicio y fin de sesión de impersonación.

Endpoints:
    - ``POST /api/auth/impersonate/{user_id}``  — iniciar impersonación
    - ``DELETE /api/auth/impersonate``           — finalizar impersonación

Requiere permiso ``impersonacion:usar`` para iniciar.
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import AuditCodes, AuditContext, audit_action
from app.core.dependencies import (
    CurrentUser,
    get_current_user,
    get_db,
    get_token_service,
)
from app.core.permissions import PermissionGrant, require_permission
from app.schemas.auth import ImpersonationTokenResponse
from app.services.token_service import TokenService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["auth"])


# ---------------------------------------------------------------------------
# POST /api/auth/impersonate/{user_id}  — iniciar impersonación
# ---------------------------------------------------------------------------


@router.post(
    "/api/auth/impersonate/{user_id}",
    response_model=ImpersonationTokenResponse,
)
async def impersonate_start(
    user_id: UUID,
    request: Request,
    grant: PermissionGrant = Depends(require_permission("impersonacion:usar")),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    token_service: TokenService = Depends(get_token_service),
) -> dict:
    """Iniciar una sesión de impersonación.

    El usuario autenticado debe tener el permiso ``impersonacion:usar``.
    El ``user_id`` debe pertenecer al mismo tenant, estar activo, y no
    ser el propio usuario.

    Devuelve un access token de impersonación (``impersonated=True``,
    ``actor_id`` del admin, ``sub`` del usuario objetivo).
    """
    # 1. No permitir impersonar si ya se está impersonando
    if current_user.impersonated:
        raise HTTPException(
            status_code=400,
            detail="Cannot impersonate while already impersonating",
        )

    # 2. No auto-impersonación
    if user_id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="Cannot impersonate yourself",
        )

    # 3. Cargar usuario objetivo y validar
    from app.models.user import User
    from app.repositories.user_repository import UserRepository

    user_repo = UserRepository()
    target_user = await user_repo.get(
        id=user_id,
        tenant_id=current_user.tenant_id,
        session=db,
    )
    if target_user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )
    if not target_user.is_active:
        raise HTTPException(
            status_code=400,
            detail="Target user is inactive",
        )

    # 4. Obtener roles vigentes del usuario objetivo
    roles = await token_service.get_vigentes_roles(
        user_id=target_user.id,
        tenant_id=target_user.tenant_id,
        session=db,
    )

    # 5. Emitir token de impersonación
    pair = await token_service.issue_token_pair(
        user=target_user,
        session=db,
        roles=roles,
        impersonated=True,
        actor_id=current_user.id,
    )

    # 6. Registrar en audit log
    ctx = AuditContext(
        actor_id=current_user.id,
        tenant_id=current_user.tenant_id,
        ip=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", ""),
        impersonado_id=target_user.id,
    )
    await audit_action(
        ctx=ctx,
        accion=AuditCodes.IMPERSONACION_INICIAR,
        detalle={"target_user_id": str(target_user.id)},
        session=db,
    )

    return {
        "access_token": pair["access_token"],
        "token_type": "bearer",
        "impersonated_user_id": str(target_user.id),
    }


# ---------------------------------------------------------------------------
# DELETE /api/auth/impersonate  — finalizar impersonación
# ---------------------------------------------------------------------------


@router.delete("/api/auth/impersonate", status_code=204)
async def impersonate_end(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Finalizar una sesión de impersonación.

    Solo puede ser invocado con un token de impersonación
    (``impersonated=True``).  Registra ``IMPERSONACION_FINALIZAR``
    en el audit log.

    No invalida el token (la invalidación real es por expiración
    del JWT, ~15 min).
    """
    if not current_user.impersonated:
        raise HTTPException(
            status_code=400,
            detail="Not an impersonation session",
        )

    ctx = AuditContext(
        actor_id=current_user.actor_id,
        tenant_id=current_user.tenant_id,
        ip=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", ""),
        impersonado_id=current_user.id,
    )
    await audit_action(
        ctx=ctx,
        accion=AuditCodes.IMPERSONACION_FINALIZAR,
        detalle={},
        session=db,
    )

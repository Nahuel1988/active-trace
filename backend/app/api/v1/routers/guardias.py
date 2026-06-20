"""Router guardias — registro y gestión de guardias docentes.

Endpoints protegidos con permiso ``guardias:registrar``.
La identidad del caller se deriva SIEMPRE del JWT verificado.
Scope: ``grant.scope`` determina si ve todo (global) o solo lo propio.
"""

from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import AuditContext
from app.core.dependencies import get_current_user, get_db
from app.core.permissions import PermissionGrant, require_permission
from app.models.guardia import EstadoGuardia
from app.schemas.guardia import (
    GuardiaCambiarEstado,
    GuardiaCreate,
    GuardiaFiltros,
    GuardiaResponse,
)
from app.services.guardia_service import GuardiaError, GuardiaService

router = APIRouter(
    prefix="/api/guardias",
    tags=["guardias"],
)


def _get_service() -> GuardiaService:
    return GuardiaService()


def _build_audit_ctx(request: Request, current_user) -> AuditContext:
    return AuditContext(
        actor_id=current_user.actor_id,
        tenant_id=current_user.tenant_id,
        ip=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", ""),
        impersonado_id=current_user.id if current_user.impersonated else None,
    )


def _build_guardia_response(g) -> GuardiaResponse:
    return GuardiaResponse(
        id=g.id,
        tenant_id=g.tenant_id,
        asignacion_id=g.asignacion_id,
        materia_id=g.materia_id,
        carrera_id=g.carrera_id,
        cohorte_id=g.cohorte_id,
        dia=g.dia,
        horario=g.horario,
        estado=g.estado,
        comentarios=g.comentarios,
        creada_at=str(g.creada_at) if g.creada_at else None,
    )


# ---------------------------------------------------------------------------
# Query param dependency
# ---------------------------------------------------------------------------


async def _parse_guardia_filtros(
    materia_id: Optional[uuid.UUID] = Query(None),
    carrera_id: Optional[uuid.UUID] = Query(None),
    cohorte_id: Optional[uuid.UUID] = Query(None),
    asignacion_id: Optional[uuid.UUID] = Query(None),
    estado: Optional[EstadoGuardia] = Query(None),
) -> GuardiaFiltros:
    return GuardiaFiltros(
        materia_id=materia_id,
        carrera_id=carrera_id,
        cohorte_id=cohorte_id,
        asignacion_id=asignacion_id,
        estado=estado,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("", response_model=GuardiaResponse, status_code=201)
async def crear_guardia(
    body: GuardiaCreate,
    request: Request,
    grant: PermissionGrant = Depends(require_permission("guardias:registrar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: GuardiaService = Depends(_get_service),
):
    """Registra una nueva guardia."""
    try:
        guardia = await service.create(
            tenant_id=current_user.tenant_id,
            actor_id=current_user.actor_id,
            is_global=grant.scope == "global",
            data=body,
            session=db,
            audit_ctx=_build_audit_ctx(request, current_user),
        )
    except GuardiaError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    return _build_guardia_response(guardia)


@router.get("", response_model=list[GuardiaResponse])
async def listar_guardias(
    filtros: GuardiaFiltros = Depends(_parse_guardia_filtros),
    grant: PermissionGrant = Depends(require_permission("guardias:registrar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: GuardiaService = Depends(_get_service),
):
    """Lista guardias según alcance del rol.

    Scope ``propio`` (TUTOR): solo guardias de sus asignaciones.
    Scope ``global`` (COORD/ADMIN): todas las del tenant.
    """
    guardias = await service.list(
        tenant_id=current_user.tenant_id,
        actor_id=current_user.actor_id,
        is_global=grant.scope == "global",
        session=db,
        materia_id=filtros.materia_id,
        carrera_id=filtros.carrera_id,
        cohorte_id=filtros.cohorte_id,
        estado=filtros.estado,
        asignacion_id=filtros.asignacion_id,
    )
    return [_build_guardia_response(g) for g in guardias]


@router.get("/{guardia_id}", response_model=GuardiaResponse)
async def obtener_guardia(
    guardia_id: uuid.UUID,
    grant: PermissionGrant = Depends(require_permission("guardias:registrar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: GuardiaService = Depends(_get_service),
):
    """Detalle de una guardia."""
    try:
        guardia = await service.get(
            tenant_id=current_user.tenant_id,
            guardia_id=guardia_id,
            actor_id=current_user.actor_id,
            is_global=grant.scope == "global",
            session=db,
        )
    except GuardiaError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    return _build_guardia_response(guardia)


@router.patch("/{guardia_id}/estado", response_model=GuardiaResponse)
async def cambiar_estado_guardia(
    guardia_id: uuid.UUID,
    body: GuardiaCambiarEstado,
    request: Request,
    grant: PermissionGrant = Depends(require_permission("guardias:registrar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: GuardiaService = Depends(_get_service),
):
    """Cambia el estado de una guardia validando la máquina de estados.

    TUTOR (scope ``propio``) no puede revertir Cancelada→Pendiente.
    """
    try:
        guardia = await service.cambiar_estado(
            tenant_id=current_user.tenant_id,
            guardia_id=guardia_id,
            nuevo_estado=body.estado,
            actor_id=current_user.actor_id,
            is_global=grant.scope == "global",
            session=db,
            audit_ctx=_build_audit_ctx(request, current_user),
        )
    except GuardiaError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    return _build_guardia_response(guardia)


@router.get("/export")
async def export_csv_guardias(
    filtros: GuardiaFiltros = Depends(_parse_guardia_filtros),
    grant: PermissionGrant = Depends(require_permission("guardias:registrar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: GuardiaService = Depends(_get_service),
):
    """Exporta guardias como CSV (solo COORDINADOR/ADMIN)."""
    if grant.scope != "global":
        raise HTTPException(
            status_code=403,
            detail="Only COORDINADOR/ADMIN can export guardias",
        )
    csv_bytes = await service.export_csv(
        tenant_id=current_user.tenant_id,
        session=db,
        materia_id=filtros.materia_id,
        carrera_id=filtros.carrera_id,
        cohorte_id=filtros.cohorte_id,
        estado=filtros.estado,
        asignacion_id=filtros.asignacion_id,
    )
    return Response(
        content=csv_bytes,
        media_type="text/csv",
        headers={
            "Content-Disposition": 'attachment; filename="guardias_export.csv"'
        },
    )

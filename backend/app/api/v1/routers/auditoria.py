"""Router auditoría — panel de métricas y log completo (solo lectura).

Todos los endpoints requieren el permiso ``auditoria:ver`` y son fail-closed.
La identidad se deriva SIEMPRE del JWT verificado (nunca de la petición).

Endpoints:
- Panel F9.1:
  GET  /api/v1/auditoria/panel/acciones-por-dia
  GET  /api/v1/auditoria/panel/comunicaciones-por-docente
  GET  /api/v1/auditoria/panel/interacciones
  GET  /api/v1/auditoria/panel/ultimas-acciones
- Log F9.2:
  GET  /api/v1/auditoria/log
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.core.permissions import PermissionGrant, require_permission
from app.schemas.auditoria import (
    AccionesPorDiaResponse,
    AccionesPorDiaItem,
    AuditoriaFiltros,
    ComunicacionesPorDocenteResponse,
    ComunicacionesPorDocenteItem,
    InteraccionesResponse,
    InteraccionesItem,
    LogResponse,
    LogItem,
    UltimasAccionesResponse,
    UltimasAccionesItem,
)
from app.services.auditoria_service import AuditoriaService

router = APIRouter(
    prefix="/api/v1/auditoria",
    tags=["auditoria"],
)


def _get_service() -> AuditoriaService:
    return AuditoriaService()


# ── Panel F9.1 ───────────────────────────────────────────────────────────────


@router.get(
    "/panel/acciones-por-dia",
    response_model=AccionesPorDiaResponse,
)
async def panel_acciones_por_dia(
    filtros: AuditoriaFiltros = Depends(),  # noqa: B008
    grant: PermissionGrant = Depends(require_permission("auditoria:ver")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: AuditoriaService = Depends(_get_service),
):
    """Serie temporal de acciones por día."""
    rows = await service.get_acciones_por_dia(
        tenant_id=current_user.tenant_id,
        session=db,
        grant=grant,
        current_user=current_user,
        desde=filtros.desde,
        hasta=filtros.hasta,
    )
    return AccionesPorDiaResponse(
        data=[AccionesPorDiaItem(**r) for r in rows],
    )


@router.get(
    "/panel/comunicaciones-por-docente",
    response_model=ComunicacionesPorDocenteResponse,
)
async def panel_comunicaciones_por_docente(
    filtros: AuditoriaFiltros = Depends(),  # noqa: B008
    grant: PermissionGrant = Depends(require_permission("auditoria:ver")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: AuditoriaService = Depends(_get_service),
):
    """Distribución de comunicaciones por docente."""
    rows = await service.get_comunicaciones_por_docente(
        tenant_id=current_user.tenant_id,
        session=db,
        grant=grant,
        current_user=current_user,
        desde=filtros.desde,
        hasta=filtros.hasta,
    )
    return ComunicacionesPorDocenteResponse(
        data=[ComunicacionesPorDocenteItem(**r) for r in rows],
    )


@router.get(
    "/panel/interacciones",
    response_model=InteraccionesResponse,
)
async def panel_interacciones(
    filtros: AuditoriaFiltros = Depends(),  # noqa: B008
    grant: PermissionGrant = Depends(require_permission("auditoria:ver")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: AuditoriaService = Depends(_get_service),
):
    """Interacciones por docente × materia."""
    rows = await service.get_interacciones(
        tenant_id=current_user.tenant_id,
        session=db,
        grant=grant,
        current_user=current_user,
        desde=filtros.desde,
        hasta=filtros.hasta,
    )
    return InteraccionesResponse(
        data=[InteraccionesItem(**r) for r in rows],
    )


@router.get(
    "/panel/ultimas-acciones",
    response_model=UltimasAccionesResponse,
)
async def panel_ultimas_acciones(
    filtros: AuditoriaFiltros = Depends(),  # noqa: B008
    grant: PermissionGrant = Depends(require_permission("auditoria:ver")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: AuditoriaService = Depends(_get_service),
):
    """Últimas N acciones del panel (defecto 200)."""
    rows = await service.get_ultimas_acciones(
        tenant_id=current_user.tenant_id,
        session=db,
        grant=grant,
        current_user=current_user,
        limit=filtros.limit,
        offset=filtros.offset,
    )
    return UltimasAccionesResponse(
        data=[UltimasAccionesItem(**r) for r in rows],
    )


# ── Log completo F9.2 ────────────────────────────────────────────────────────


@router.get(
    "/log",
    response_model=LogResponse,
)
async def log_completo(
    filtros: AuditoriaFiltros = Depends(),  # noqa: B008
    grant: PermissionGrant = Depends(require_permission("auditoria:ver")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: AuditoriaService = Depends(_get_service),
):
    """Log completo de auditoría paginado y filtrable.

    Filtros: rango de fechas, materia, usuario, código de acción.
    El scope del permiso (``global`` vs ``propio``) se aplica
    automáticamente.
    """
    rows = await service.get_log(
        tenant_id=current_user.tenant_id,
        session=db,
        grant=grant,
        current_user=current_user,
        desde=filtros.desde,
        hasta=filtros.hasta,
        materia_id=filtros.materia_id,
        actor_id=filtros.actor_id,
        accion=filtros.accion,
        limit=filtros.limit,
        offset=filtros.offset,
    )
    return LogResponse(
        data=[LogItem(**r) for r in rows],
    )

"""Router de monitores transversales — general y seguimiento.

Endpoints:
  GET /api/v1/monitores/general       — monitor general (coord/admin)
  GET /api/v1/monitores/seguimiento   — monitor de seguimiento (tutor/prof/coord/admin)
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import AuditCodes, AuditContext, audit_action
from app.core.dependencies import get_current_user, get_db
from app.core.permissions import PermissionGrant, require_permission
from app.schemas.analisis import MonitorResponse
from app.services.monitor_service import MonitorError, MonitorService

router = APIRouter(prefix="/api/v1/monitores", tags=["monitores"])


def _get_monitor_service() -> MonitorService:
    return MonitorService()


def _build_audit_ctx(request: Request, current_user) -> AuditContext:
    return AuditContext(
        actor_id=current_user.actor_id,
        tenant_id=current_user.tenant_id,
        ip=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", ""),
        impersonado_id=current_user.id if getattr(current_user, "impersonated", False) else None,
    )


@router.get("/general", response_model=MonitorResponse)
async def get_monitor_general(
    materia_id: str | None = Query(None, description="UUID de la materia (opcional)"),
    regional: str | None = Query(None, description="Filtrar por regional"),
    comision: str | None = Query(None, description="Filtrar por comisión"),
    q: str | None = Query(None, description="Búsqueda libre (nombre/apellido)"),
    estado: str | None = Query(None, description="Filtrar por estado: atrasado"),
    limit: int = Query(50, ge=1, le=200, description="Máximo resultados"),
    offset: int = Query(0, ge=0, description="Desplazamiento"),
    format: str = Query("json", description="Formato: json o csv"),
    grant: PermissionGrant = Depends(require_permission("atrasados:ver")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
    service: MonitorService = Depends(_get_monitor_service),
):
    """Retorna vista general de todos los alumnos del tenant (F2.7)."""
    try:
        resultado = await service.get_monitor_general(
            tenant_id=current_user.tenant_id,
            materia_id=UUID(materia_id) if materia_id else None,
            regional=regional,
            comision=comision,
            q=q,
            estado=estado,
            limit=limit,
            offset=offset,
            session=db,
        )
    except MonitorError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)

    audit_ctx = _build_audit_ctx(request, current_user)
    await audit_action(
        ctx=audit_ctx,
        accion=AuditCodes.MONITOR_CONSULTAR,
        session=db,
        detalle={
            "endpoint": "monitor-general",
            "materia_id": materia_id,
            "regional": regional,
            "comision": comision,
            "estado": estado,
            "format": format,
        },
    )

    if format == "csv":
        from fastapi.responses import PlainTextResponse
        csv_content = await service.export_monitor_csv(
            tenant_id=current_user.tenant_id,
            items=resultado.items,
            session=db,
        )
        return PlainTextResponse(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=monitor-general.csv"},
        )

    return resultado


@router.get("/seguimiento", response_model=MonitorResponse)
async def get_monitor_seguimiento(
    materia_id: str | None = Query(None, description="UUID de la materia (opcional)"),
    comision: str | None = Query(None, description="Filtrar por comisión"),
    q: str | None = Query(None, description="Búsqueda libre (nombre/apellido)"),
    estado: str | None = Query(None, description="Filtrar por estado: atrasado"),
    fecha_desde: str | None = Query(None, description="Fecha inicio (YYYY-MM-DD)"),
    fecha_hasta: str | None = Query(None, description="Fecha fin (YYYY-MM-DD)"),
    limit: int = Query(50, ge=1, le=200, description="Máximo resultados"),
    offset: int = Query(0, ge=0, description="Desplazamiento"),
    format: str = Query("json", description="Formato: json o csv"),
    grant: PermissionGrant = Depends(require_permission("atrasados:ver")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
    service: MonitorService = Depends(_get_monitor_service),
):
    """Retorna vista de seguimiento scoped al usuario (F2.8, F2.9)."""
    try:
        resultado = await service.get_monitor_seguimiento(
            tenant_id=current_user.tenant_id,
            user_id=current_user.actor_id,
            materia_id=UUID(materia_id) if materia_id else None,
            comision=comision,
            q=q,
            estado=estado,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            limit=limit,
            offset=offset,
            session=db,
        )
    except MonitorError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)

    audit_ctx = _build_audit_ctx(request, current_user)
    await audit_action(
        ctx=audit_ctx,
        accion=AuditCodes.MONITOR_CONSULTAR,
        session=db,
        detalle={
            "endpoint": "monitor-seguimiento",
            "materia_id": materia_id,
            "comision": comision,
            "estado": estado,
            "format": format,
        },
    )

    if format == "csv":
        from fastapi.responses import PlainTextResponse
        csv_content = await service.export_monitor_csv(
            tenant_id=current_user.tenant_id,
            items=resultado.items,
            session=db,
        )
        return PlainTextResponse(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=monitor-seguimiento.csv"},
        )

    return resultado




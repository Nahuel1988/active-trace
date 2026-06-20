"""Router de análisis académico — atrasados, ranking, reportes, notas finales.

Endpoints:
  GET /api/v1/analisis/atrasados          — alumnos atrasados por materia×cohorte
  GET /api/v1/analisis/ranking            — ranking de actividades aprobadas
  GET /api/v1/analisis/reportes           — métricas rápidas por materia
  GET /api/v1/analisis/notas-finales      — notas finales agrupadas
  GET /api/v1/analisis/entregas-pendientes — entregas sin corregir
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import AuditCodes, AuditContext, audit_action
from app.core.dependencies import get_current_user, get_db
from app.core.permissions import PermissionGrant, require_permission
from app.schemas.analisis import (
    AtrasadosResponse,
    EntregasPendientesResponse,
    NotasFinalesResponse,
    RankingResponse,
    ReporteRapidoResponse,
)
from app.services.analisis_service import AnalisisError, AnalisisService

router = APIRouter(prefix="/api/v1/analisis", tags=["analisis"])


def _get_analisis_service() -> AnalisisService:
    return AnalisisService()


def _build_audit_ctx(request: Request, current_user) -> AuditContext:
    return AuditContext(
        actor_id=current_user.actor_id,
        tenant_id=current_user.tenant_id,
        ip=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", ""),
        impersonado_id=current_user.id if getattr(current_user, "impersonated", False) else None,
    )


@router.get("/atrasados", response_model=AtrasadosResponse)
async def get_atrasados(
    materia_id: str = Query(..., description="UUID de la materia"),
    cohorte_id: str | None = Query(None, description="UUID de la cohorte (opcional)"),
    grant: PermissionGrant = Depends(require_permission("atrasados:ver")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
    service: AnalisisService = Depends(_get_analisis_service),
):
    """Retorna alumnos atrasados para una materia×cohorte."""
    try:
        materia_uuid = UUID(materia_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="materia_id inválido")

    cohorte_uuid = None
    if cohorte_id:
        try:
            cohorte_uuid = UUID(cohorte_id)
        except ValueError:
            raise HTTPException(status_code=422, detail="cohorte_id inválido")

    try:
        resultado = await service.get_atrasados(
            tenant_id=current_user.tenant_id,
            materia_id=materia_uuid,
            cohorte_id=cohorte_uuid,
            session=db,
        )
    except AnalisisError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)

    audit_ctx = _build_audit_ctx(request, current_user)
    await audit_action(
        ctx=audit_ctx,
        accion=AuditCodes.ANALISIS_CONSULTAR,
        session=db,
        detalle={
            "endpoint": "atrasados",
            "materia_id": materia_id,
            "cohorte_id": cohorte_id,
            "total": resultado.total,
        },
        materia_id=materia_uuid,
    )

    return resultado


@router.get("/ranking", response_model=RankingResponse)
async def get_ranking(
    materia_id: str = Query(..., description="UUID de la materia"),
    cohorte_id: str | None = Query(None, description="UUID de la cohorte (opcional)"),
    grant: PermissionGrant = Depends(require_permission("atrasados:ver")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
    service: AnalisisService = Depends(_get_analisis_service),
):
    """Retorna ranking de actividades aprobadas por alumno."""
    try:
        materia_uuid = UUID(materia_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="materia_id inválido")

    cohorte_uuid = None
    if cohorte_id:
        try:
            cohorte_uuid = UUID(cohorte_id)
        except ValueError:
            raise HTTPException(status_code=422, detail="cohorte_id inválido")

    try:
        resultado = await service.get_ranking(
            tenant_id=current_user.tenant_id,
            materia_id=materia_uuid,
            cohorte_id=cohorte_uuid,
            session=db,
        )
    except AnalisisError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)

    audit_ctx = _build_audit_ctx(request, current_user)
    await audit_action(
        ctx=audit_ctx,
        accion=AuditCodes.ANALISIS_CONSULTAR,
        session=db,
        detalle={
            "endpoint": "ranking",
            "materia_id": materia_id,
            "cohorte_id": cohorte_id,
        },
        materia_id=materia_uuid,
    )

    return resultado


@router.get("/reportes", response_model=ReporteRapidoResponse)
async def get_reporte_rapido(
    materia_id: str = Query(..., description="UUID de la materia"),
    cohorte_id: str | None = Query(None, description="UUID de la cohorte (opcional)"),
    grant: PermissionGrant = Depends(require_permission("atrasados:ver")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
    service: AnalisisService = Depends(_get_analisis_service),
):
    """Retorna métricas rápidas de una materia×cohorte."""
    try:
        materia_uuid = UUID(materia_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="materia_id inválido")

    cohorte_uuid = None
    if cohorte_id:
        try:
            cohorte_uuid = UUID(cohorte_id)
        except ValueError:
            raise HTTPException(status_code=422, detail="cohorte_id inválido")

    try:
        resultado = await service.get_reporte_rapido(
            tenant_id=current_user.tenant_id,
            materia_id=materia_uuid,
            cohorte_id=cohorte_uuid,
            session=db,
        )
    except AnalisisError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)

    audit_ctx = _build_audit_ctx(request, current_user)
    await audit_action(
        ctx=audit_ctx,
        accion=AuditCodes.ANALISIS_CONSULTAR,
        session=db,
        detalle={
            "endpoint": "reportes",
            "materia_id": materia_id,
            "cohorte_id": cohorte_id,
        },
        materia_id=materia_uuid,
    )

    return resultado


@router.get("/notas-finales")
async def get_notas_finales(
    materia_id: str = Query(..., description="UUID de la materia"),
    cohorte_id: str | None = Query(None, description="UUID de la cohorte (opcional)"),
    format: str = Query("json", description="Formato: json o csv"),
    grant: PermissionGrant = Depends(require_permission("atrasados:ver")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
    service: AnalisisService = Depends(_get_analisis_service),
):
    """Retorna notas finales agrupadas por alumno."""
    try:
        materia_uuid = UUID(materia_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="materia_id inválido")

    cohorte_uuid = None
    if cohorte_id:
        try:
            cohorte_uuid = UUID(cohorte_id)
        except ValueError:
            raise HTTPException(status_code=422, detail="cohorte_id inválido")

    try:
        resultado = await service.get_notas_finales(
            tenant_id=current_user.tenant_id,
            materia_id=materia_uuid,
            cohorte_id=cohorte_uuid,
            format=format,
            session=db,
        )
    except AnalisisError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)

    audit_ctx = _build_audit_ctx(request, current_user)
    await audit_action(
        ctx=audit_ctx,
        accion=AuditCodes.ANALISIS_CONSULTAR if format == "json" else AuditCodes.ANALISIS_EXPORTAR,
        session=db,
        detalle={
            "endpoint": "notas-finales",
            "materia_id": materia_id,
            "cohorte_id": cohorte_id,
            "format": format,
        },
        materia_id=materia_uuid,
    )

    if format == "csv":
        from fastapi.responses import PlainTextResponse
        return PlainTextResponse(
            content=resultado,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=notas-finales.csv"},
        )

    return resultado


@router.get("/entregas-pendientes", response_model=EntregasPendientesResponse)
async def get_entregas_pendientes(
    materia_id: str = Query(..., description="UUID de la materia"),
    cohorte_id: str | None = Query(None, description="UUID de la cohorte (opcional)"),
    grant: PermissionGrant = Depends(require_permission("atrasados:ver")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
    service: AnalisisService = Depends(_get_analisis_service),
):
    """Retorna actividades textuales sin calificar."""
    try:
        materia_uuid = UUID(materia_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="materia_id inválido")

    cohorte_uuid = None
    if cohorte_id:
        try:
            cohorte_uuid = UUID(cohorte_id)
        except ValueError:
            raise HTTPException(status_code=422, detail="cohorte_id inválido")

    try:
        resultado = await service.get_entregas_pendientes(
            tenant_id=current_user.tenant_id,
            materia_id=materia_uuid,
            cohorte_id=cohorte_uuid,
            session=db,
        )
    except AnalisisError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)

    audit_ctx = _build_audit_ctx(request, current_user)
    await audit_action(
        ctx=audit_ctx,
        accion=AuditCodes.ANALISIS_EXPORTAR,
        session=db,
        detalle={
            "endpoint": "entregas-pendientes",
            "materia_id": materia_id,
            "cohorte_id": cohorte_id,
            "todas_corregidas": resultado.todas_corregidas,
        },
        materia_id=materia_uuid,
    )

    return resultado

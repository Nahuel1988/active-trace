"""Router para Liquidaciones de honorarios docentes.

Endpoints:
  POST /calcular           → liquidaciones:calcular
  GET  /                   → liquidaciones:ver
  GET  /{id}               → liquidaciones:ver
  POST /{id}/cerrar        → liquidaciones:cerrar
  GET  /historial          → liquidaciones:ver
  POST /exportar           → liquidaciones:exportar
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import AuditContext
from app.core.dependencies import get_current_user, get_db
from app.core.permissions import require_permission
from app.schemas.liquidacion import (
    CalculoRequest,
    LiquidacionResumen,
    LiquidacionResponse,
    LiquidacionSegmentadaResponse,
)
from app.services.liquidacion_service import LiquidacionError, LiquidacionService

router = APIRouter(
    prefix="/api/v1/liquidaciones",
    tags=["Liquidaciones"],
)


def _svc() -> LiquidacionService:
    return LiquidacionService()


def _map_error(exc: LiquidacionError) -> HTTPException:
    return HTTPException(status_code=exc.status_code, detail=exc.detail)


def _audit_ctx(request: Request, current_user) -> AuditContext:
    return AuditContext(
        actor_id=current_user.actor_id,
        tenant_id=current_user.tenant_id,
        ip=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", ""),
        impersonado_id=current_user.id if current_user.impersonated else None,
    )


@router.post("/calcular", response_model=LiquidacionResumen, status_code=200)
async def calcular_liquidaciones(
    body: CalculoRequest,
    _grant=Depends(require_permission("liquidaciones:calcular")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    svc: LiquidacionService = Depends(_svc),
):
    """Calcula (o recalcula) liquidaciones para una cohorte en un período."""
    try:
        return await svc.calcular(
            tenant_id=current_user.tenant_id,
            cohorte_id=body.cohorte_id,
            periodo=body.periodo,
            session=db,
        )
    except LiquidacionError as exc:
        raise _map_error(exc) from exc


@router.get("", response_model=LiquidacionSegmentadaResponse)
async def obtener_liquidaciones(
    cohorte_id: UUID = Query(...),
    periodo: str = Query(...),
    usuario_id: UUID | None = Query(None),
    _grant=Depends(require_permission("liquidaciones:ver")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    svc: LiquidacionService = Depends(_svc),
):
    """Retorna liquidaciones segmentadas (general, nexo, facturantes) con KPIs."""
    try:
        return await svc.obtener_liquidaciones(
            tenant_id=current_user.tenant_id,
            cohorte_id=cohorte_id,
            periodo=periodo,
            session=db,
            usuario_id=usuario_id,
        )
    except LiquidacionError as exc:
        raise _map_error(exc) from exc


@router.get("/historial", response_model=list[LiquidacionResponse])
async def obtener_historial(
    cohorte_id: UUID | None = Query(None),
    periodo: str | None = Query(None),
    usuario_id: UUID | None = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    _grant=Depends(require_permission("liquidaciones:ver")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    svc: LiquidacionService = Depends(_svc),
):
    """Retorna historial de liquidaciones Cerradas."""
    return await svc.obtener_historial(
        tenant_id=current_user.tenant_id,
        session=db,
        cohorte_id=cohorte_id,
        periodo=periodo,
        usuario_id=usuario_id,
        limit=limit,
        offset=offset,
    )


@router.get("/{liquidacion_id}", response_model=LiquidacionResponse)
async def obtener_liquidacion(
    liquidacion_id: UUID,
    _grant=Depends(require_permission("liquidaciones:ver")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    svc: LiquidacionService = Depends(_svc),
):
    """Obtiene una liquidación por ID."""
    from app.repositories.liquidacion_repository import LiquidacionRepository

    repo = LiquidacionRepository()
    liq = await repo.get(id=liquidacion_id, tenant_id=current_user.tenant_id, session=db)
    if liq is None:
        raise HTTPException(status_code=404, detail="Liquidación no encontrada")
    return LiquidacionResponse.model_validate(liq)


@router.post("/{liquidacion_id}/cerrar", response_model=LiquidacionResponse)
async def cerrar_liquidacion(
    liquidacion_id: UUID,
    request: Request,
    _grant=Depends(require_permission("liquidaciones:cerrar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    svc: LiquidacionService = Depends(_svc),
):
    """Cierra una Liquidacion (Abierta → Cerrada). Registra auditoría."""
    try:
        return await svc.cerrar(
            tenant_id=current_user.tenant_id,
            liquidacion_id=liquidacion_id,
            session=db,
            audit_ctx=_audit_ctx(request, current_user),
        )
    except LiquidacionError as exc:
        raise _map_error(exc) from exc


@router.post("/exportar", response_model=list[dict])
async def exportar_liquidaciones(
    body: CalculoRequest,
    _grant=Depends(require_permission("liquidaciones:exportar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    svc: LiquidacionService = Depends(_svc),
):
    """Exporta liquidaciones en formato plano (formato definitivo en C-24)."""
    return await svc.exportar(
        tenant_id=current_user.tenant_id,
        cohorte_id=body.cohorte_id,
        periodo=body.periodo,
        session=db,
    )

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import AuditCodes, AuditContext
from app.core.dependencies import get_current_user, get_db
from app.core.permissions import PermissionGrant, require_permission
from app.models.comunicacion import EstadoComunicacion
from app.schemas.comunicacion import (
    ComunicacionCreate,
    ComunicacionFiltros,
    ComunicacionResponse,
    LoteActionResponse,
    LoteResponse,
    PreviewRequest,
    PreviewResponse,
)
from app.services.comunicacion_service import ComunicacionError, ComunicacionService


router = APIRouter(
    prefix="/api/comunicaciones",
    tags=["comunicaciones"],
)


def _get_comunicacion_service() -> ComunicacionService:
    return ComunicacionService()


async def _parse_filtros(
    estado: Optional[EstadoComunicacion] = Query(None),
    lote_id: Optional[UUID] = Query(None),
    materia_id: Optional[UUID] = Query(None),
    enviado_por: Optional[UUID] = Query(None),
    desde: Optional[str] = Query(None),
    hasta: Optional[str] = Query(None),
) -> ComunicacionFiltros:
    return ComunicacionFiltros(
        estado=estado,
        lote_id=lote_id,
        materia_id=materia_id,
        enviado_por=enviado_por,
    )


def _build_audit_ctx(request: Request, current_user) -> AuditContext:
    return AuditContext(
        actor_id=current_user.actor_id,
        tenant_id=current_user.tenant_id,
        ip=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", ""),
        impersonado_id=current_user.id if current_user.impersonated else None,
    )


def _map_error(exc: ComunicacionError) -> HTTPException:
    return HTTPException(status_code=exc.status_code, detail=exc.detail)


@router.get("", response_model=list[ComunicacionResponse])
async def listar_comunicaciones(
    filtros: ComunicacionFiltros = Depends(_parse_filtros),
    grant: PermissionGrant = Depends(require_permission("comunicacion:enviar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: ComunicacionService = Depends(_get_comunicacion_service),
):
    scope_user_id = current_user.id if grant.scope == "propio" else None
    comunicaciones = await service.list(
        tenant_id=current_user.tenant_id,
        filtros=filtros,
        scope_user_id=scope_user_id,
        session=db,
    )
    return [ComunicacionResponse.model_validate(c) for c in comunicaciones]


@router.post("/preview", response_model=PreviewResponse)
async def preview_comunicacion(
    body: PreviewRequest,
    grant: PermissionGrant = Depends(require_permission("comunicacion:enviar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: ComunicacionService = Depends(_get_comunicacion_service),
):
    try:
        return await service.preview(data=body)
    except ComunicacionError as exc:
        raise _map_error(exc) from exc


@router.post("", response_model=LoteResponse, status_code=201)
async def crear_comunicacion(
    request: Request,
    body: ComunicacionCreate,
    grant: PermissionGrant = Depends(require_permission("comunicacion:enviar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: ComunicacionService = Depends(_get_comunicacion_service),
):
    try:
        lote = await service.crear_lote(
            tenant_id=current_user.tenant_id,
            enviado_por=current_user.actor_id,
            data=body,
            session=db,
        )
    except ComunicacionError as exc:
        raise _map_error(exc) from exc
    return lote


@router.get("/lote/{lote_id}", response_model=LoteResponse)
async def obtener_lote(
    lote_id: UUID,
    grant: PermissionGrant = Depends(require_permission("comunicacion:enviar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: ComunicacionService = Depends(_get_comunicacion_service),
):
    try:
        return await service.obtener_lote(
            tenant_id=current_user.tenant_id,
            lote_id=lote_id,
            session=db,
        )
    except ComunicacionError as exc:
        raise _map_error(exc) from exc


@router.post("/{comunicacion_id}/aprobar", response_model=ComunicacionResponse)
async def aprobar_comunicacion(
    comunicacion_id: UUID,
    grant: PermissionGrant = Depends(require_permission("comunicacion:aprobar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: ComunicacionService = Depends(_get_comunicacion_service),
):
    try:
        comunicacion = await service.aprobar(
            tenant_id=current_user.tenant_id,
            comunicacion_id=comunicacion_id,
            session=db,
        )
    except ComunicacionError as exc:
        raise _map_error(exc) from exc
    return ComunicacionResponse.model_validate(comunicacion)


@router.post("/{comunicacion_id}/cancelar", response_model=ComunicacionResponse)
async def cancelar_comunicacion(
    comunicacion_id: UUID,
    grant: PermissionGrant = Depends(require_permission("comunicacion:enviar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: ComunicacionService = Depends(_get_comunicacion_service),
):
    try:
        comunicacion = await service.cancelar(
            tenant_id=current_user.tenant_id,
            comunicacion_id=comunicacion_id,
            session=db,
        )
    except ComunicacionError as exc:
        raise _map_error(exc) from exc
    return ComunicacionResponse.model_validate(comunicacion)


@router.post("/lote/{lote_id}/aprobar", response_model=LoteActionResponse)
async def aprobar_lote(
    lote_id: UUID,
    grant: PermissionGrant = Depends(require_permission("comunicacion:aprobar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: ComunicacionService = Depends(_get_comunicacion_service),
):
    try:
        return await service.aprobar_lote(
            tenant_id=current_user.tenant_id,
            lote_id=lote_id,
            session=db,
        )
    except ComunicacionError as exc:
        raise _map_error(exc) from exc


@router.post("/lote/{lote_id}/cancelar", response_model=LoteActionResponse)
async def cancelar_lote(
    lote_id: UUID,
    grant: PermissionGrant = Depends(require_permission("comunicacion:enviar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: ComunicacionService = Depends(_get_comunicacion_service),
):
    try:
        return await service.cancelar_lote(
            tenant_id=current_user.tenant_id,
            lote_id=lote_id,
            session=db,
        )
    except ComunicacionError as exc:
        raise _map_error(exc) from exc

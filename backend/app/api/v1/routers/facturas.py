"""Router para Facturas de docentes monotributistas.

Endpoints:
  GET  /           → facturas:gestionar
  POST /           → facturas:gestionar
  GET  /{id}       → facturas:gestionar
  PUT  /{id}       → facturas:gestionar
  POST /{id}/abonar → facturas:gestionar
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.core.permissions import require_permission
from app.schemas.factura import FacturaCreate, FacturaResponse, FacturaUpdate
from app.services.factura_service import FacturaError, FacturaService

router = APIRouter(
    prefix="/api/v1/facturas",
    tags=["Facturas"],
)


def _svc() -> FacturaService:
    return FacturaService()


def _map_error(exc: FacturaError) -> HTTPException:
    return HTTPException(status_code=exc.status_code, detail=exc.detail)


@router.get("", response_model=list[FacturaResponse])
async def listar_facturas(
    periodo: str | None = Query(None),
    estado: str | None = Query(None),
    usuario_id: UUID | None = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    _grant=Depends(require_permission("facturas:gestionar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    svc: FacturaService = Depends(_svc),
):
    """Lista facturas con filtros opcionales."""
    return await svc.listar_facturas(
        tenant_id=current_user.tenant_id,
        session=db,
        periodo=periodo,
        estado=estado,
        usuario_id=usuario_id,
        limit=limit,
        offset=offset,
    )


@router.post("", response_model=FacturaResponse, status_code=201)
async def crear_factura(
    body: FacturaCreate,
    _grant=Depends(require_permission("facturas:gestionar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    svc: FacturaService = Depends(_svc),
):
    """Crea una nueva factura para un docente facturador."""
    try:
        return await svc.crear_factura(
            tenant_id=current_user.tenant_id, data=body, session=db
        )
    except FacturaError as exc:
        raise _map_error(exc) from exc


@router.get("/{factura_id}", response_model=FacturaResponse)
async def obtener_factura(
    factura_id: UUID,
    _grant=Depends(require_permission("facturas:gestionar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    svc: FacturaService = Depends(_svc),
):
    """Obtiene una factura por ID."""
    try:
        return await svc.obtener_factura(
            tenant_id=current_user.tenant_id, factura_id=factura_id, session=db
        )
    except FacturaError as exc:
        raise _map_error(exc) from exc


@router.put("/{factura_id}", response_model=FacturaResponse)
async def actualizar_factura(
    factura_id: UUID,
    body: FacturaUpdate,
    _grant=Depends(require_permission("facturas:gestionar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    svc: FacturaService = Depends(_svc),
):
    """Actualiza una Factura (solo si está Pendiente)."""
    try:
        return await svc.actualizar_factura(
            tenant_id=current_user.tenant_id,
            factura_id=factura_id,
            data=body,
            session=db,
        )
    except FacturaError as exc:
        raise _map_error(exc) from exc


@router.post("/{factura_id}/abonar", response_model=FacturaResponse)
async def abonar_factura(
    factura_id: UUID,
    _grant=Depends(require_permission("facturas:gestionar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    svc: FacturaService = Depends(_svc),
):
    """Transiciona una Factura de Pendiente a Abonada."""
    try:
        return await svc.abonar(
            tenant_id=current_user.tenant_id, factura_id=factura_id, session=db
        )
    except FacturaError as exc:
        raise _map_error(exc) from exc

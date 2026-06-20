"""Router para la Grilla Salarial (SalarioBase y SalarioPlus).

Todos los endpoints requieren permiso 'grilla:operar' (FINANZAS).
Identidad siempre desde JWT; nunca desde parámetros.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.core.permissions import require_permission
from app.schemas.salario_base import SalarioBaseCreate, SalarioBaseResponse, SalarioBaseUpdate
from app.schemas.salario_plus import SalarioPlusCreate, SalarioPlusResponse, SalarioPlusUpdate
from app.services.grilla_service import GrillaError, GrillaService

router = APIRouter(
    prefix="/api/v1/grilla",
    tags=["Grilla Salarial"],
)


def _svc() -> GrillaService:
    return GrillaService()


def _map_error(exc: GrillaError) -> HTTPException:
    return HTTPException(status_code=exc.status_code, detail=exc.detail)


# ─── SalarioBase ──────────────────────────────────────────────────────────


@router.get("/salarios-base", response_model=list[SalarioBaseResponse])
async def listar_salarios_base(
    rol: str | None = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    _grant=Depends(require_permission("grilla:operar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    svc: GrillaService = Depends(_svc),
):
    """Lista salarios base del tenant con filtro opcional por rol."""
    items = await svc.listar_salarios_base(
        tenant_id=current_user.tenant_id,
        session=db,
        rol=rol,
        limit=limit,
        offset=offset,
    )
    return [SalarioBaseResponse.model_validate(i) for i in items]


@router.post("/salarios-base", response_model=SalarioBaseResponse, status_code=201)
async def crear_salario_base(
    body: SalarioBaseCreate,
    _grant=Depends(require_permission("grilla:operar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    svc: GrillaService = Depends(_svc),
):
    """Crea un nuevo SalarioBase con validación de solapamiento de vigencia."""
    try:
        sb = await svc.configurar_salario_base(
            tenant_id=current_user.tenant_id, data=body, session=db
        )
    except GrillaError as exc:
        raise _map_error(exc) from exc
    return SalarioBaseResponse.model_validate(sb)


@router.put("/salarios-base/{salario_id}", response_model=SalarioBaseResponse)
async def actualizar_salario_base(
    salario_id: UUID,
    body: SalarioBaseUpdate,
    _grant=Depends(require_permission("grilla:operar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    svc: GrillaService = Depends(_svc),
):
    """Actualiza monto y/o vigencia de un SalarioBase."""
    try:
        sb = await svc.actualizar_salario_base(
            tenant_id=current_user.tenant_id,
            salario_id=salario_id,
            data=body,
            session=db,
        )
    except GrillaError as exc:
        raise _map_error(exc) from exc
    return SalarioBaseResponse.model_validate(sb)


@router.delete("/salarios-base/{salario_id}", status_code=204)
async def eliminar_salario_base(
    salario_id: UUID,
    _grant=Depends(require_permission("grilla:operar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    svc: GrillaService = Depends(_svc),
):
    """Soft-delete de un SalarioBase."""
    try:
        await svc.eliminar_salario_base(
            tenant_id=current_user.tenant_id, salario_id=salario_id, session=db
        )
    except GrillaError as exc:
        raise _map_error(exc) from exc


# ─── SalarioPlus ──────────────────────────────────────────────────────────


@router.get("/salarios-plus", response_model=list[SalarioPlusResponse])
async def listar_salarios_plus(
    grupo: str | None = Query(None),
    rol: str | None = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    _grant=Depends(require_permission("grilla:operar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    svc: GrillaService = Depends(_svc),
):
    """Lista plus salariales del tenant con filtros opcionales."""
    items = await svc.listar_salarios_plus(
        tenant_id=current_user.tenant_id,
        session=db,
        grupo=grupo,
        rol=rol,
        limit=limit,
        offset=offset,
    )
    return [SalarioPlusResponse.model_validate(i) for i in items]


@router.post("/salarios-plus", response_model=SalarioPlusResponse, status_code=201)
async def crear_salario_plus(
    body: SalarioPlusCreate,
    _grant=Depends(require_permission("grilla:operar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    svc: GrillaService = Depends(_svc),
):
    """Crea un nuevo SalarioPlus con validación de solapamiento."""
    try:
        sp = await svc.configurar_salario_plus(
            tenant_id=current_user.tenant_id, data=body, session=db
        )
    except GrillaError as exc:
        raise _map_error(exc) from exc
    return SalarioPlusResponse.model_validate(sp)


@router.put("/salarios-plus/{plus_id}", response_model=SalarioPlusResponse)
async def actualizar_salario_plus(
    plus_id: UUID,
    body: SalarioPlusUpdate,
    _grant=Depends(require_permission("grilla:operar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    svc: GrillaService = Depends(_svc),
):
    """Actualiza descripción, monto y/o vigencia de un SalarioPlus."""
    try:
        sp = await svc.actualizar_salario_plus(
            tenant_id=current_user.tenant_id, plus_id=plus_id, data=body, session=db
        )
    except GrillaError as exc:
        raise _map_error(exc) from exc
    return SalarioPlusResponse.model_validate(sp)


@router.delete("/salarios-plus/{plus_id}", status_code=204)
async def eliminar_salario_plus(
    plus_id: UUID,
    _grant=Depends(require_permission("grilla:operar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    svc: GrillaService = Depends(_svc),
):
    """Soft-delete de un SalarioPlus."""
    try:
        await svc.eliminar_salario_plus(
            tenant_id=current_user.tenant_id, plus_id=plus_id, session=db
        )
    except GrillaError as exc:
        raise _map_error(exc) from exc

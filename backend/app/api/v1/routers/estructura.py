"""Estructura académica router — carreras, cohortes, materias.

Endpoints protegidos por el permiso "estructura:gestionar".
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.core.permissions import PermissionGrant, require_permission
from app.schemas import estructura as schemas
from app.services.carrera_service import CarreraService, ServiceError as CarreraError
from app.services.cohorte_service import CohorteService, CohorteError
from app.services.materia_service import MateriaService, MateriaError


router = APIRouter(
    prefix="/api/v1/estructura",
    tags=["estructura"],
)


def _get_carrera_service() -> CarreraService:
    return CarreraService()


def _get_cohorte_service() -> CohorteService:
    return CohorteService()


def _get_materia_service() -> MateriaService:
    return MateriaService()


def _carrera_to_response(c) -> schemas.CarreraResponse:
    return schemas.CarreraResponse(
        id=str(c.id),
        tenant_id=str(c.tenant_id),
        codigo=c.codigo,
        nombre=c.nombre,
        estado=str(c.estado.value) if hasattr(c.estado, "value") else str(c.estado),
        created_at=c.created_at,
        updated_at=c.updated_at,
    )


def _cohorte_to_response(c) -> schemas.CohorteResponse:
    return schemas.CohorteResponse(
        id=str(c.id),
        tenant_id=str(c.tenant_id),
        carrera_id=str(c.carrera_id),
        nombre=c.nombre,
        anio=c.anio,
        vig_desde=c.vig_desde,
        vig_hasta=c.vig_hasta,
        estado=str(c.estado.value) if hasattr(c.estado, "value") else str(c.estado),
        created_at=c.created_at,
        updated_at=c.updated_at,
    )


def _materia_to_response(m) -> schemas.MateriaResponse:
    return schemas.MateriaResponse(
        id=str(m.id),
        tenant_id=str(m.tenant_id),
        codigo=m.codigo,
        nombre=m.nombre,
        estado=str(m.estado.value) if hasattr(m.estado, "value") else str(m.estado),
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


@router.get("/carreras", response_model=list[schemas.CarreraResponse])
async def listar_carreras(
    grant: PermissionGrant = Depends(require_permission("estructura:gestionar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: CarreraService = Depends(_get_carrera_service),
):
    carreras = await service.list(tenant_id=current_user.tenant_id, session=db)
    return [_carrera_to_response(c) for c in carreras]


@router.post("/carreras", response_model=schemas.CarreraResponse, status_code=201)
async def crear_carrera(
    body: schemas.CarreraCreate,
    grant: PermissionGrant = Depends(require_permission("estructura:gestionar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: CarreraService = Depends(_get_carrera_service),
):
    try:
        c = await service.create(tenant_id=current_user.tenant_id, data=body.model_dump(), session=db)
    except CarreraError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    return _carrera_to_response(c)


@router.get("/cohortes", response_model=list[schemas.CohorteResponse])
async def listar_cohortes(
    grant: PermissionGrant = Depends(require_permission("estructura:gestionar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: CohorteService = Depends(_get_cohorte_service),
):
    cohortes = await service.list(tenant_id=current_user.tenant_id, session=db)
    return [_cohorte_to_response(c) for c in cohortes]


@router.post("/cohortes", response_model=schemas.CohorteResponse, status_code=201)
async def crear_cohorte(
    body: schemas.CohorteCreate,
    grant: PermissionGrant = Depends(require_permission("estructura:gestionar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: CohorteService = Depends(_get_cohorte_service),
):
    try:
        c = await service.create(tenant_id=current_user.tenant_id, data=body.model_dump(), session=db)
    except CohorteError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    return _cohorte_to_response(c)


@router.get("/materias", response_model=list[schemas.MateriaResponse])
async def listar_materias(
    grant: PermissionGrant = Depends(require_permission("estructura:gestionar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: MateriaService = Depends(_get_materia_service),
):
    materias = await service._repo.list_all(tenant_id=current_user.tenant_id, session=db)
    return [_materia_to_response(m) for m in materias]


@router.post("/materias", response_model=schemas.MateriaResponse, status_code=201)
async def crear_materia(
    body: schemas.MateriaCreate,
    grant: PermissionGrant = Depends(require_permission("estructura:gestionar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: MateriaService = Depends(_get_materia_service),
):
    try:
        m = await service.create(tenant_id=current_user.tenant_id, data=body.model_dump(), session=db)
    except MateriaError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    return _materia_to_response(m)

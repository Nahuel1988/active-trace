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


@router.get("/carreras", response_model=list[schemas.CarreraResponse])
async def listar_carreras(
    grant: PermissionGrant = Depends(require_permission("estructura:gestionar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: CarreraService = Depends(_get_carrera_service),
):
    carreras = await service.list(tenant_id=current_user.tenant_id, session=db)
    return [schemas.CarreraResponse.from_orm(c) for c in carreras]


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

    return schemas.CarreraResponse.from_orm(c)


@router.get("/cohortes", response_model=list[schemas.CohorteResponse])
async def listar_cohortes(
    grant: PermissionGrant = Depends(require_permission("estructura:gestionar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: CohorteService = Depends(_get_cohorte_service),
):
    # CohorteService does not implement list; use repository via service if added later.
    # For now return empty list to keep router minimal and test permission guards.
    return []


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
    return schemas.CohorteResponse.from_orm(c)


@router.get("/materias", response_model=list[schemas.MateriaResponse])
async def listar_materias(
    grant: PermissionGrant = Depends(require_permission("estructura:gestionar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: MateriaService = Depends(_get_materia_service),
):
    # MateriaService does not implement list; return empty list for now.
    return []


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

    return schemas.MateriaResponse.from_orm(m)

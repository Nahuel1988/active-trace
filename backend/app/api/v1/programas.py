"""Programas router — CRUD de programas de materia."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.core.permissions import PermissionGrant, require_permission
from app.schemas import programa_materia as schemas
from app.services.programa_materia_service import ProgramaMateriaService, ServiceError


router = APIRouter(
    prefix="/api/v1/programas",
    tags=["programas"],
)


def _get_service() -> ProgramaMateriaService:
    return ProgramaMateriaService()


@router.post("", response_model=schemas.ProgramaMateriaResponse, status_code=201)
async def crear_programa(
    body: schemas.ProgramaMateriaCreate,
    grant: PermissionGrant = Depends(require_permission("estructura:gestionar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: ProgramaMateriaService = Depends(_get_service),
):
    try:
        obj = await service.create(
            tenant_id=current_user.tenant_id,
            data=body.model_dump(),
            session=db,
        )
    except ServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    return schemas.ProgramaMateriaResponse(
        id=str(obj.id),
        tenant_id=str(obj.tenant_id),
        materia_id=str(obj.materia_id),
        carrera_id=str(obj.carrera_id),
        cohorte_id=str(obj.cohorte_id),
        titulo=obj.titulo,
        referencia_archivo=obj.referencia_archivo,
        cargado_at=obj.cargado_at.isoformat(),
        created_at=obj.created_at.isoformat(),
        updated_at=obj.updated_at.isoformat(),
    )


@router.get("", response_model=list[schemas.ProgramaMateriaResponse])
async def listar_programas(
    grant: PermissionGrant = Depends(require_permission("estructura:ver")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: ProgramaMateriaService = Depends(_get_service),
    materia_id: UUID | None = Query(default=None),
    carrera_id: UUID | None = Query(default=None),
    cohorte_id: UUID | None = Query(default=None),
):
    objs = await service.list(
        tenant_id=current_user.tenant_id,
        session=db,
        materia_id=materia_id,
        carrera_id=carrera_id,
        cohorte_id=cohorte_id,
    )
    return [
        schemas.ProgramaMateriaResponse(
            id=str(o.id), tenant_id=str(o.tenant_id),
            materia_id=str(o.materia_id), carrera_id=str(o.carrera_id),
            cohorte_id=str(o.cohorte_id), titulo=o.titulo,
            referencia_archivo=o.referencia_archivo,
            cargado_at=o.cargado_at.isoformat(),
            created_at=o.created_at.isoformat(),
            updated_at=o.updated_at.isoformat(),
        )
        for o in objs
    ]


@router.get("/{id}", response_model=schemas.ProgramaMateriaResponse)
async def obtener_programa(
    id: UUID,
    grant: PermissionGrant = Depends(require_permission("estructura:ver")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: ProgramaMateriaService = Depends(_get_service),
):
    try:
        obj = await service.get(tenant_id=current_user.tenant_id, id=id, session=db)
    except ServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    return schemas.ProgramaMateriaResponse(
        id=str(obj.id), tenant_id=str(obj.tenant_id),
        materia_id=str(obj.materia_id), carrera_id=str(obj.carrera_id),
        cohorte_id=str(obj.cohorte_id), titulo=obj.titulo,
        referencia_archivo=obj.referencia_archivo,
        cargado_at=obj.cargado_at.isoformat(),
        created_at=obj.created_at.isoformat(),
        updated_at=obj.updated_at.isoformat(),
    )


@router.put("/{id}", response_model=schemas.ProgramaMateriaResponse)
async def actualizar_programa(
    id: UUID,
    body: schemas.ProgramaMateriaUpdate,
    grant: PermissionGrant = Depends(require_permission("estructura:gestionar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: ProgramaMateriaService = Depends(_get_service),
):
    try:
        obj = await service.update(
            tenant_id=current_user.tenant_id,
            id=id,
            data=body.model_dump(exclude_unset=True),
            session=db,
        )
    except ServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    return schemas.ProgramaMateriaResponse(
        id=str(obj.id), tenant_id=str(obj.tenant_id),
        materia_id=str(obj.materia_id), carrera_id=str(obj.carrera_id),
        cohorte_id=str(obj.cohorte_id), titulo=obj.titulo,
        referencia_archivo=obj.referencia_archivo,
        cargado_at=obj.cargado_at.isoformat(),
        created_at=obj.created_at.isoformat(),
        updated_at=obj.updated_at.isoformat(),
    )


@router.delete("/{id}", status_code=204)
async def eliminar_programa(
    id: UUID,
    grant: PermissionGrant = Depends(require_permission("estructura:gestionar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: ProgramaMateriaService = Depends(_get_service),
):
    deleted = await service.delete(tenant_id=current_user.tenant_id, id=id, session=db)
    if not deleted:
        raise HTTPException(status_code=404, detail="not found")
    return None

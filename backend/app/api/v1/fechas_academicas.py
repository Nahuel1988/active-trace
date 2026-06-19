"""Fechas académicas router — CRUD, calendario y fragmento LMS."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.core.permissions import PermissionGrant, require_permission
from app.schemas import fecha_academica as schemas
from app.services.fecha_academica_service import (
    FechaAcademicaService,
    FechaAcademicaError,
    build_lms_fragment,
)


router = APIRouter(
    prefix="/api/v1/fechas-academicas",
    tags=["fechas-academicas"],
)


def _get_service() -> FechaAcademicaService:
    return FechaAcademicaService()


@router.post("", response_model=schemas.FechaAcademicaResponse, status_code=201)
async def crear_fecha(
    body: schemas.FechaAcademicaCreate,
    grant: PermissionGrant = Depends(require_permission("estructura:gestionar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: FechaAcademicaService = Depends(_get_service),
):
    try:
        obj = await service.create(
            tenant_id=current_user.tenant_id,
            data=body.model_dump(),
            session=db,
        )
    except FechaAcademicaError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    return schemas.FechaAcademicaResponse(
        id=str(obj.id), tenant_id=str(obj.tenant_id),
        materia_id=str(obj.materia_id), cohorte_id=str(obj.cohorte_id),
        tipo=obj.tipo, numero=obj.numero,
        periodo=obj.periodo, fecha=obj.fecha.isoformat(),
        titulo=obj.titulo,
        created_at=obj.created_at.isoformat(),
        updated_at=obj.updated_at.isoformat(),
    )


@router.get("", response_model=list[schemas.FechaAcademicaResponse])
async def listar_fechas(
    grant: PermissionGrant = Depends(require_permission("estructura:ver")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: FechaAcademicaService = Depends(_get_service),
    materia_id: UUID | None = Query(default=None),
    cohorte_id: UUID | None = Query(default=None),
    periodo: str | None = Query(default=None),
    tipo: str | None = Query(default=None),
):
    objs = await service.list_tabular(
        tenant_id=current_user.tenant_id,
        session=db,
        materia_id=materia_id,
        cohorte_id=cohorte_id,
        periodo=periodo,
        tipo=tipo,
    )
    return [
        schemas.FechaAcademicaResponse(
            id=str(o.id), tenant_id=str(o.tenant_id),
            materia_id=str(o.materia_id), cohorte_id=str(o.cohorte_id),
            tipo=o.tipo, numero=o.numero, periodo=o.periodo,
            fecha=o.fecha.isoformat(), titulo=o.titulo,
            created_at=o.created_at.isoformat(),
            updated_at=o.updated_at.isoformat(),
        )
        for o in objs
    ]


@router.get("/calendario")
async def calendario_fechas(
    grant: PermissionGrant = Depends(require_permission("estructura:ver")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: FechaAcademicaService = Depends(_get_service),
    materia_id: UUID | None = Query(default=None),
    cohorte_id: UUID | None = Query(default=None),
):
    return await service.list_calendario(
        tenant_id=current_user.tenant_id,
        session=db,
        materia_id=materia_id,
        cohorte_id=cohorte_id,
    )


@router.get("/lms-fragment")
async def lms_fragment(
    grant: PermissionGrant = Depends(require_permission("estructura:ver")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: FechaAcademicaService = Depends(_get_service),
    materia_id: UUID = Query(...),
    cohorte_id: UUID = Query(...),
):
    fechas = await service.list_tabular(
        tenant_id=current_user.tenant_id,
        session=db,
        materia_id=materia_id,
        cohorte_id=cohorte_id,
    )
    fragment = build_lms_fragment(fechas)
    return {"fragment": fragment}


@router.get("/{id}", response_model=schemas.FechaAcademicaResponse)
async def obtener_fecha(
    id: UUID,
    grant: PermissionGrant = Depends(require_permission("estructura:ver")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: FechaAcademicaService = Depends(_get_service),
):
    obj = await service.get(tenant_id=current_user.tenant_id, id=id, session=db)
    if obj is None:
        raise HTTPException(status_code=404, detail="not found")
    return schemas.FechaAcademicaResponse(
        id=str(obj.id), tenant_id=str(obj.tenant_id),
        materia_id=str(obj.materia_id), cohorte_id=str(obj.cohorte_id),
        tipo=obj.tipo, numero=obj.numero, periodo=obj.periodo,
        fecha=obj.fecha.isoformat(), titulo=obj.titulo,
        created_at=obj.created_at.isoformat(),
        updated_at=obj.updated_at.isoformat(),
    )


@router.put("/{id}", response_model=schemas.FechaAcademicaResponse)
async def actualizar_fecha(
    id: UUID,
    body: schemas.FechaAcademicaUpdate,
    grant: PermissionGrant = Depends(require_permission("estructura:gestionar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: FechaAcademicaService = Depends(_get_service),
):
    try:
        obj = await service.update(
            tenant_id=current_user.tenant_id,
            id=id,
            data=body.model_dump(exclude_unset=True),
            session=db,
        )
    except FechaAcademicaError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    return schemas.FechaAcademicaResponse(
        id=str(obj.id), tenant_id=str(obj.tenant_id),
        materia_id=str(obj.materia_id), cohorte_id=str(obj.cohorte_id),
        tipo=obj.tipo, numero=obj.numero, periodo=obj.periodo,
        fecha=obj.fecha.isoformat(), titulo=obj.titulo,
        created_at=obj.created_at.isoformat(),
        updated_at=obj.updated_at.isoformat(),
    )


@router.delete("/{id}", status_code=204)
async def eliminar_fecha(
    id: UUID,
    grant: PermissionGrant = Depends(require_permission("estructura:gestionar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: FechaAcademicaService = Depends(_get_service),
):
    deleted = await service.delete(tenant_id=current_user.tenant_id, id=id, session=db)
    if not deleted:
        raise HTTPException(status_code=404, detail="not found")
    return None

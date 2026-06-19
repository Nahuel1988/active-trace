"""Avisos router — gestión y visualización de avisos del sistema."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.core.permissions import PermissionGrant, require_permission
from app.repositories.acknowledgment_repository import AcknowledgmentRepository
from app.schemas import avisos as schemas
from app.services.aviso_service import AvisoService, ServiceError as AvisoError
from app.services.acknowledgment_service import AcknowledgmentService


router = APIRouter(
    prefix="/api/v1/avisos",
    tags=["avisos"],
)


def _get_service() -> AvisoService:
    return AvisoService()


def _get_ack_service() -> AcknowledgmentService:
    return AcknowledgmentService()


@router.get("/", response_model=list[schemas.AvisoResponse])
async def listar_avisos(
    grant: PermissionGrant = Depends(require_permission("avisos:publicar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: AvisoService = Depends(_get_service),
):
    avisos = await service.list(tenant_id=current_user.tenant_id, session=db)
    result = []
    for a in avisos:
        total_acks, total_visibles = await service.get_contadores(aviso_id=a.id, session=db)
        resp = schemas.AvisoResponse.model_validate(a)
        resp.total_acks = total_acks
        resp.total_visibles = total_visibles
        result.append(resp)
    return result


@router.post("/", response_model=schemas.AvisoResponse, status_code=201)
async def crear_aviso(
    body: schemas.AvisoCreate,
    grant: PermissionGrant = Depends(require_permission("avisos:publicar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: AvisoService = Depends(_get_service),
):
    try:
        a = await service.create(tenant_id=current_user.tenant_id, data=body.model_dump(), session=db)
    except AvisoError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    return schemas.AvisoResponse.model_validate(a)


@router.get("/visibles", response_model=list[schemas.AvisoVisibleResponse])
async def listar_avisos_visibles(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: AvisoService = Depends(_get_service),
):
    avisos = await service.list_visibles(
        tenant_id=current_user.tenant_id,
        usuario_id=current_user.id,
        materia_ids=[],
        cohorte_ids=[],
        roles=[],
        session=db,
    )
    result = []
    ack_repo = AcknowledgmentRepository()
    for a in avisos:
        resp = schemas.AvisoVisibleResponse.model_validate(a)
        resp.acknowledged = await ack_repo.exists(
            tenant_id=current_user.tenant_id,
            aviso_id=a.id,
            usuario_id=current_user.id,
            session=db,
        )
        result.append(resp)
    return result


@router.get("/{id}", response_model=schemas.AvisoResponse)
async def obtener_aviso(
    id: str,
    grant: PermissionGrant = Depends(require_permission("avisos:publicar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: AvisoService = Depends(_get_service),
):
    try:
        a = await service.get(tenant_id=current_user.tenant_id, id=uuid.UUID(id), session=db)
    except AvisoError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    total_acks, total_visibles = await service.get_contadores(aviso_id=a.id, session=db)
    resp = schemas.AvisoResponse.model_validate(a)
    resp.total_acks = total_acks
    resp.total_visibles = total_visibles
    return resp


@router.put("/{id}", response_model=schemas.AvisoResponse)
async def actualizar_aviso(
    id: str,
    body: schemas.AvisoUpdate,
    grant: PermissionGrant = Depends(require_permission("avisos:publicar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: AvisoService = Depends(_get_service),
):
    try:
        a = await service.update(
            tenant_id=current_user.tenant_id,
            id=uuid.UUID(id),
            data=body.model_dump(exclude_unset=True),
            session=db,
        )
    except AvisoError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    return schemas.AvisoResponse.model_validate(a)


@router.delete("/{id}", status_code=204)
async def eliminar_aviso(
    id: str,
    grant: PermissionGrant = Depends(require_permission("avisos:publicar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: AvisoService = Depends(_get_service),
):
    deleted = await service.delete(tenant_id=current_user.tenant_id, id=uuid.UUID(id), session=db)
    if not deleted:
        raise HTTPException(status_code=404, detail="not found")


@router.post("/{id}/ack", response_model=schemas.AckResponse, status_code=201)
async def confirmar_lectura(
    id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    ack_service: AcknowledgmentService = Depends(_get_ack_service),
):
    try:
        ack = await ack_service.confirmar(
            tenant_id=current_user.tenant_id,
            aviso_id=uuid.UUID(id),
            usuario_id=current_user.id,
            session=db,
        )
    except AvisoError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    return schemas.AckResponse.model_validate(ack)

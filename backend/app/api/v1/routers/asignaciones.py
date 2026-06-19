"""Router asignaciones — CRUD de asignaciones usuario×rol×contexto.

Endpoints protegidos por el permiso 'equipos:asignar'.
La identidad del caller se deriva SIEMPRE del JWT verificado.
El sub-objeto usuario en la response NO contiene PII sensible (UsuarioMinimo).

GET    /api/v1/asignaciones
GET    /api/v1/asignaciones/{id}
POST   /api/v1/asignaciones
PUT    /api/v1/asignaciones/{id}
DELETE /api/v1/asignaciones/{id}
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.core.permissions import PermissionGrant, require_permission
from app.schemas.asignacion import AsignacionCreate, AsignacionResponse, AsignacionUpdate
from app.schemas.usuario import UsuarioMinimo
from app.services.asignacion_service import AsignacionService, AsignacionServiceError

router = APIRouter(
    prefix="/api/v1/asignaciones",
    tags=["asignaciones"],
)


def _get_service() -> AsignacionService:
    return AsignacionService()


async def _build_response(asig, db: AsyncSession) -> AsignacionResponse:
    """Construye AsignacionResponse con sub-objeto UsuarioMinimo (sin PII)."""
    from app.repositories.usuario_repository import UsuarioRepository

    usuario_repo = UsuarioRepository()
    user = await usuario_repo.get(
        id=asig.usuario_id, tenant_id=asig.tenant_id, session=db
    )

    usuario_minimo = UsuarioMinimo(
        id=str(asig.usuario_id),
        nombre=user.nombre if user else None,
        apellidos=user.apellidos if user else None,
        legajo=user.legajo if user else None,
    )

    return AsignacionResponse(
        id=str(asig.id),
        tenant_id=str(asig.tenant_id),
        usuario_id=str(asig.usuario_id),
        role_id=str(asig.role_id),
        materia_id=str(asig.materia_id) if asig.materia_id else None,
        carrera_id=str(asig.carrera_id) if asig.carrera_id else None,
        cohorte_id=str(asig.cohorte_id) if asig.cohorte_id else None,
        comisiones=asig.comisiones or [],
        responsable_id=str(asig.responsable_id) if asig.responsable_id else None,
        desde=asig.desde,
        hasta=asig.hasta,
        estado_vigencia=asig.estado_vigencia,
        usuario=usuario_minimo,
        created_at=asig.created_at,
        updated_at=asig.updated_at,
    )


@router.get("", response_model=list[AsignacionResponse])
async def listar_asignaciones(
    usuario_id: Optional[uuid.UUID] = Query(default=None),
    materia_id: Optional[uuid.UUID] = Query(default=None),
    carrera_id: Optional[uuid.UUID] = Query(default=None),
    cohorte_id: Optional[uuid.UUID] = Query(default=None),
    rol: Optional[str] = Query(default=None),
    responsable_id: Optional[uuid.UUID] = Query(default=None),
    estado_vigencia: str = Query(default="vigente", pattern="^(vigente|vencida|todas)$"),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0),
    grant: PermissionGrant = Depends(require_permission("equipos:asignar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: AsignacionService = Depends(_get_service),
):
    """Lista asignaciones del tenant con filtros y control de vigencia."""
    asignaciones = await service.list(
        tenant_id=current_user.tenant_id,
        session=db,
        estado_vigencia=estado_vigencia,
        usuario_id=usuario_id,
        materia_id=materia_id,
        carrera_id=carrera_id,
        cohorte_id=cohorte_id,
        responsable_id=responsable_id,
        limit=limit,
        offset=offset,
    )

    return [await _build_response(a, db) for a in asignaciones]


@router.get("/{id}", response_model=AsignacionResponse)
async def obtener_asignacion(
    id: uuid.UUID,
    grant: PermissionGrant = Depends(require_permission("equipos:asignar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: AsignacionService = Depends(_get_service),
):
    """Retorna una asignación por ID."""
    try:
        asig = await service.get(
            tenant_id=current_user.tenant_id, id=id, session=db
        )
    except AsignacionServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    return await _build_response(asig, db)


@router.post("", response_model=AsignacionResponse, status_code=201)
async def crear_asignacion(
    body: AsignacionCreate,
    grant: PermissionGrant = Depends(require_permission("equipos:asignar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: AsignacionService = Depends(_get_service),
):
    """Crea una nueva asignación con validación de rol × contexto."""
    from app.repositories.base import BaseRepository
    from app.models.role import Role

    # Resolver role_code desde role_id para validación de contexto
    from sqlalchemy import select
    stmt = select(Role).where(
        Role.id == uuid.UUID(body.role_id),  # type: ignore[arg-type]
        Role.tenant_id == current_user.tenant_id,
        Role.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    role = result.scalar_one_or_none()
    if role is None:
        raise HTTPException(status_code=404, detail="role not found")

    try:
        asig = await service.create(
            tenant_id=current_user.tenant_id,
            actor_id=current_user.id,
            usuario_id=uuid.UUID(body.usuario_id),
            role_id=uuid.UUID(body.role_id),
            role_code=role.code,
            desde=body.desde,
            hasta=body.hasta,
            materia_id=uuid.UUID(body.materia_id) if body.materia_id else None,
            carrera_id=uuid.UUID(body.carrera_id) if body.carrera_id else None,
            cohorte_id=uuid.UUID(body.cohorte_id) if body.cohorte_id else None,
            responsable_id=uuid.UUID(body.responsable_id) if body.responsable_id else None,
            comisiones=body.comisiones,
            session=db,
        )
    except AsignacionServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    return await _build_response(asig, db)


@router.delete("/{id}", status_code=204)
async def eliminar_asignacion(
    id: uuid.UUID,
    grant: PermissionGrant = Depends(require_permission("equipos:asignar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: AsignacionService = Depends(_get_service),
):
    """Soft delete de una asignación. El histórico se conserva."""
    try:
        await service.delete(
            tenant_id=current_user.tenant_id,
            id=id,
            actor_id=current_user.id,
            session=db,
        )
    except AsignacionServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

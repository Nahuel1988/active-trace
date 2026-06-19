"""Router de tareas internas (C-16).

Endpoints protegidos por ``require_permission("tareas:gestionar")``.
Prefix: ``/api/tareas`` (registrado en main.py).
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import AuditCodes, AuditContext
from app.core.dependencies import get_current_user, get_db
from app.core.permissions import PermissionGrant, require_permission
from app.models.tarea import EstadoTarea
from app.schemas.tarea import (
    ComentarioCreate,
    ComentarioResponse,
    TareaCambiarEstado,
    TareaCreate,
    TareaDelegar,
    TareaFiltros,
    TareaResponse,
)
from app.services.comentario_tarea_service import (
    ComentarioError,
    ComentarioTareaService,
)
from app.services.tarea_service import TareaError, TareaService


router = APIRouter(
    prefix="/api/tareas",
    tags=["tareas-internas"],
)


# ---------------------------------------------------------------------------
# Service factories
# ---------------------------------------------------------------------------


def _get_tarea_service() -> TareaService:
    return TareaService()


def _get_comentario_service() -> ComentarioTareaService:
    return ComentarioTareaService()


# ---------------------------------------------------------------------------
# Query param dependency for TareaFiltros
# ---------------------------------------------------------------------------


async def _parse_filtros(
    asignado_a: Optional[UUID] = Query(None),
    asignado_por: Optional[UUID] = Query(None),
    materia_id: Optional[UUID] = Query(None),
    estado: Optional[EstadoTarea] = Query(None),
    q: Optional[str] = Query(None),
) -> TareaFiltros:
    return TareaFiltros(
        asignado_a=asignado_a,
        asignado_por=asignado_por,
        materia_id=materia_id,
        estado=estado,
        q=q,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_audit_ctx(request: Request, current_user) -> AuditContext:
    return AuditContext(
        actor_id=current_user.actor_id,
        tenant_id=current_user.tenant_id,
        ip=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", ""),
        impersonado_id=current_user.id if current_user.impersonated else None,
    )


def _map_tarea_error(exc: TareaError) -> HTTPException:
    return HTTPException(status_code=exc.status_code, detail=exc.detail)


def _map_comentario_error(exc: ComentarioError) -> HTTPException:
    return HTTPException(status_code=exc.status_code, detail=exc.detail)


# ---------------------------------------------------------------------------
# Endpoints — Tareas
# ---------------------------------------------------------------------------


@router.get("/mias", response_model=list[TareaResponse])
async def mis_tareas(
    grant: PermissionGrant = Depends(require_permission("tareas:gestionar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: TareaService = Depends(_get_tarea_service),
):
    """Retorna las tareas asignadas al usuario autenticado (``asignado_a``)."""
    tareas = await service.list_mias(
        tenant_id=current_user.tenant_id,
        usuario_id=current_user.id,
        session=db,
    )
    return [TareaResponse.model_validate(t) for t in tareas]


@router.get("", response_model=list[TareaResponse])
async def listar_tareas(
    filtros: TareaFiltros = Depends(_parse_filtros),
    grant: PermissionGrant = Depends(require_permission("tareas:gestionar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: TareaService = Depends(_get_tarea_service),
):
    """Lista tareas con filtros opcionales.

    El alcance depende del rol (vía PermissionGrant):
    - "propio" (PROFESOR): solo tareas donde participa.
    - "global" (COORD/ADMIN): todas las del tenant.
    """
    scope_user_id = current_user.id if grant.scope == "propio" else None
    tareas = await service.list(
        tenant_id=current_user.tenant_id,
        filtros=filtros,
        scope_user_id=scope_user_id,
        session=db,
    )
    return [TareaResponse.model_validate(t) for t in tareas]


@router.post("", response_model=TareaResponse, status_code=201)
async def crear_tarea(
    request: Request,
    body: TareaCreate,
    grant: PermissionGrant = Depends(require_permission("tareas:gestionar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: TareaService = Depends(_get_tarea_service),
):
    """Crea una nueva tarea interna.

    ``asignado_por`` se toma de la sesión JWT, nunca del body.
    """
    try:
        tarea = await service.create(
            tenant_id=current_user.tenant_id,
            asignado_por=current_user.actor_id,
            data=body,
            session=db,
            audit_ctx=_build_audit_ctx(request, current_user),
        )
    except TareaError as exc:
        raise _map_tarea_error(exc) from exc

    return TareaResponse.model_validate(tarea)


@router.get("/{tarea_id}", response_model=TareaResponse)
async def obtener_tarea(
    tarea_id: UUID,
    grant: PermissionGrant = Depends(require_permission("tareas:gestionar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: TareaService = Depends(_get_tarea_service),
):
    """Obtiene una tarea por ID. 404 si no existe o fuera de alcance."""
    try:
        tarea = await service.get(
            tenant_id=current_user.tenant_id,
            tarea_id=tarea_id,
            scope_user_id=current_user.id if grant.scope == "propio" else None,
            session=db,
        )
    except TareaError as exc:
        raise _map_tarea_error(exc) from exc

    return TareaResponse.model_validate(tarea)


@router.delete("/{tarea_id}", status_code=204)
async def eliminar_tarea(
    tarea_id: UUID,
    grant: PermissionGrant = Depends(require_permission("tareas:gestionar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: TareaService = Depends(_get_tarea_service),
):
    """Soft-delete de una tarea."""
    deleted = await service.delete(
        tenant_id=current_user.tenant_id,
        tarea_id=tarea_id,
        session=db,
    )
    if not deleted:
        raise HTTPException(status_code=404, detail="Tarea not found")


@router.post("/{tarea_id}/asignar", response_model=TareaResponse)
async def delegar_tarea(
    request: Request,
    tarea_id: UUID,
    body: TareaDelegar,
    grant: PermissionGrant = Depends(require_permission("tareas:gestionar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: TareaService = Depends(_get_tarea_service),
):
    """Delega/re-asigna una tarea a otro usuario.

    El nuevo ``asignado_a`` debe pertenecer al mismo tenant.
    """
    try:
        tarea = await service.delegar(
            tenant_id=current_user.tenant_id,
            tarea_id=tarea_id,
            nuevo_asignado_a=body.asignado_a,
            actor=current_user.actor_id,
            scope=grant.scope,
            session=db,
            audit_ctx=_build_audit_ctx(request, current_user),
        )
    except TareaError as exc:
        raise _map_tarea_error(exc) from exc

    return TareaResponse.model_validate(tarea)


@router.patch("/{tarea_id}/estado", response_model=TareaResponse)
async def cambiar_estado_tarea(
    request: Request,
    tarea_id: UUID,
    body: TareaCambiarEstado,
    grant: PermissionGrant = Depends(require_permission("tareas:gestionar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: TareaService = Depends(_get_tarea_service),
):
    """Cambia el estado de una tarea validando la máquina de estados.

    PROFESOR (scope "propio") no puede reabrir tareas resueltas.
    """
    try:
        tarea = await service.cambiar_estado(
            tenant_id=current_user.tenant_id,
            tarea_id=tarea_id,
            nuevo_estado=body.estado,
            actor=current_user.actor_id,
            scope=grant.scope,
            session=db,
            audit_ctx=_build_audit_ctx(request, current_user),
        )
    except TareaError as exc:
        raise _map_tarea_error(exc) from exc

    return TareaResponse.model_validate(tarea)


# ---------------------------------------------------------------------------
# Endpoints — Comentarios
# ---------------------------------------------------------------------------


@router.get("/{tarea_id}/comentarios", response_model=list[ComentarioResponse])
async def listar_comentarios(
    tarea_id: UUID,
    grant: PermissionGrant = Depends(require_permission("tareas:gestionar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: ComentarioTareaService = Depends(_get_comentario_service),
):
    """Lista los comentarios de una tarea en orden cronológico ascendente."""
    try:
        comentarios = await service.listar(
            tenant_id=current_user.tenant_id,
            tarea_id=tarea_id,
            session=db,
            scope_user_id=current_user.id if grant.scope == "propio" else None,
        )
    except ComentarioError as exc:
        raise _map_comentario_error(exc) from exc

    return [ComentarioResponse.model_validate(c) for c in comentarios]


@router.post("/{tarea_id}/comentarios", response_model=ComentarioResponse, status_code=201)
async def crear_comentario(
    request: Request,
    tarea_id: UUID,
    body: ComentarioCreate,
    grant: PermissionGrant = Depends(require_permission("tareas:gestionar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: ComentarioTareaService = Depends(_get_comentario_service),
):
    """Agrega un comentario a una tarea.

    ``autor_id`` se toma de la sesión JWT, nunca del body.
    Los comentarios son append-only (no se editan ni borran).
    """
    try:
        comentario = await service.crear(
            tenant_id=current_user.tenant_id,
            tarea_id=tarea_id,
            autor_id=current_user.actor_id,
            texto=body.texto,
            session=db,
            scope_user_id=current_user.id if grant.scope == "propio" else None,
        )
    except ComentarioError as exc:
        raise _map_comentario_error(exc) from exc

    return ComentarioResponse.model_validate(comentario)

"""Router encuentros — gestión de slots e instancias de encuentros.

Endpoints protegidos con permiso ``encuentros:gestionar``.
La identidad del caller se deriva SIEMPRE del JWT verificado.
Scope: ``grant.scope`` determina si ve todo (global) o solo lo propio.
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import AuditContext
from app.core.dependencies import get_current_user, get_db
from app.core.permissions import PermissionGrant, require_permission
from app.models.instancia_encuentro import EstadoInstancia
from app.schemas.slot_encuentro import (
    InstanciaEdit,
    InstanciaResponse,
    SlotCreate,
    SlotResponse,
)
from app.services.encuentro_service import EncuentroError, EncuentroService

router = APIRouter(
    prefix="/api/encuentros",
    tags=["encuentros"],
)


def _get_service() -> EncuentroService:
    return EncuentroService()


def _build_audit_ctx(request: Request, current_user) -> AuditContext:
    return AuditContext(
        actor_id=current_user.actor_id,
        tenant_id=current_user.tenant_id,
        ip=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", ""),
        impersonado_id=current_user.id if current_user.impersonated else None,
    )


def _build_slot_response(slot) -> SlotResponse:
    instancias = []
    for inst in getattr(slot, "instancias", []) or []:
        instancias.append(_build_instancia_response(inst))
    return SlotResponse(
        id=slot.id,
        tenant_id=slot.tenant_id,
        asignacion_id=slot.asignacion_id,
        materia_id=slot.materia_id,
        titulo=slot.titulo,
        hora=slot.hora,
        dia_semana=slot.dia_semana,
        fecha_inicio=slot.fecha_inicio,
        cant_semanas=slot.cant_semanas,
        fecha_unica=slot.fecha_unica,
        meet_url=slot.meet_url,
        vig_desde=slot.vig_desde,
        vig_hasta=slot.vig_hasta,
        instancias=instancias,
        created_at=str(slot.created_at) if slot.created_at else None,
        updated_at=str(slot.updated_at) if slot.updated_at else None,
    )


def _build_instancia_response(inst) -> InstanciaResponse:
    return InstanciaResponse(
        id=inst.id,
        tenant_id=inst.tenant_id,
        slot_id=inst.slot_id,
        materia_id=inst.materia_id,
        fecha=inst.fecha,
        hora=inst.hora,
        titulo=inst.titulo,
        estado=inst.estado,
        meet_url=inst.meet_url,
        video_url=inst.video_url,
        comentario=inst.comentario,
        slot_titulo=getattr(inst, "slot_titulo", None),
        created_at=str(inst.created_at) if inst.created_at else None,
        updated_at=str(inst.updated_at) if inst.updated_at else None,
    )


# ---------------------------------------------------------------------------
# Endpoints — Slots
# ---------------------------------------------------------------------------


@router.post("/slots", response_model=SlotResponse, status_code=201)
async def crear_slot(
    body: SlotCreate,
    request: Request,
    grant: PermissionGrant = Depends(require_permission("encuentros:gestionar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: EncuentroService = Depends(_get_service),
):
    """Crea un slot (recurrente o único) con generación automática de instancias."""
    try:
        slot = await service.create_slot(
            tenant_id=current_user.tenant_id,
            actor_id=current_user.actor_id,
            is_global=grant.scope == "global",
            data=body,
            session=db,
            audit_ctx=_build_audit_ctx(request, current_user),
        )
    except EncuentroError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    return _build_slot_response(slot)


@router.get("/slots", response_model=list[SlotResponse])
async def listar_slots(
    materia_id: Optional[uuid.UUID] = Query(default=None),
    grant: PermissionGrant = Depends(require_permission("encuentros:gestionar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: EncuentroService = Depends(_get_service),
):
    """Lista slots del tenant. Scope ``propio`` solo ve sus slots."""
    slots = await service.list_slots(
        tenant_id=current_user.tenant_id,
        actor_id=current_user.actor_id,
        is_global=grant.scope == "global",
        session=db,
        materia_id=materia_id,
    )
    return [_build_slot_response(s) for s in slots]


@router.get("/slots/{slot_id}", response_model=SlotResponse)
async def obtener_slot(
    slot_id: uuid.UUID,
    grant: PermissionGrant = Depends(require_permission("encuentros:gestionar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: EncuentroService = Depends(_get_service),
):
    """Detalle de un slot con sus instancias."""
    try:
        slot = await service.get_slot(
            tenant_id=current_user.tenant_id,
            slot_id=slot_id,
            actor_id=current_user.actor_id,
            is_global=grant.scope == "global",
            session=db,
        )
    except EncuentroError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    return _build_slot_response(slot)


@router.delete("/slots/{slot_id}", status_code=204)
async def eliminar_slot(
    slot_id: uuid.UUID,
    grant: PermissionGrant = Depends(require_permission("encuentros:gestionar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: EncuentroService = Depends(_get_service),
):
    """Soft delete de un slot."""
    try:
        await service.delete_slot(
            tenant_id=current_user.tenant_id,
            slot_id=slot_id,
            actor_id=current_user.actor_id,
            is_global=grant.scope == "global",
            session=db,
        )
    except EncuentroError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


# ---------------------------------------------------------------------------
# Endpoints — Instancias
# ---------------------------------------------------------------------------


@router.get("/instancias", response_model=list[InstanciaResponse])
async def listar_instancias(
    slot_id: Optional[uuid.UUID] = Query(default=None),
    materia_id: Optional[uuid.UUID] = Query(default=None),
    estado: Optional[EstadoInstancia] = Query(default=None),
    fecha_desde: Optional[date] = Query(default=None),
    fecha_hasta: Optional[date] = Query(default=None),
    grant: PermissionGrant = Depends(require_permission("encuentros:gestionar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: EncuentroService = Depends(_get_service),
):
    """Lista instancias con filtros. Scope ``propio`` ve solo las propias."""
    instancias = await service.list_instancias(
        tenant_id=current_user.tenant_id,
        actor_id=current_user.actor_id,
        is_global=grant.scope == "global",
        session=db,
        slot_id=slot_id,
        materia_id=materia_id,
        estado=estado,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
    )
    return [_build_instancia_response(i) for i in instancias]


@router.get("/instancias/{instancia_id}", response_model=InstanciaResponse)
async def obtener_instancia(
    instancia_id: uuid.UUID,
    grant: PermissionGrant = Depends(require_permission("encuentros:gestionar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: EncuentroService = Depends(_get_service),
):
    """Detalle de una instancia."""
    try:
        instancia = await service.get_instancia(
            tenant_id=current_user.tenant_id,
            instancia_id=instancia_id,
            actor_id=current_user.actor_id,
            is_global=grant.scope == "global",
            session=db,
        )
    except EncuentroError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    return _build_instancia_response(instancia)


@router.patch("/instancias/{instancia_id}", response_model=InstanciaResponse)
async def editar_instancia(
    instancia_id: uuid.UUID,
    body: InstanciaEdit,
    request: Request,
    grant: PermissionGrant = Depends(require_permission("encuentros:gestionar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: EncuentroService = Depends(_get_service),
):
    """Edita campos editables de una instancia (estado, meet_url, video_url, comentario)."""
    try:
        instancia = await service.edit_instancia(
            tenant_id=current_user.tenant_id,
            instancia_id=instancia_id,
            data=body,
            actor_id=current_user.actor_id,
            is_global=grant.scope == "global",
            session=db,
            audit_ctx=_build_audit_ctx(request, current_user),
        )
    except EncuentroError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    return _build_instancia_response(instancia)


# ---------------------------------------------------------------------------
# Endpoints — Export HTML
# ---------------------------------------------------------------------------


@router.get("/slots/{slot_id}/html")
async def export_html_slot(
    slot_id: uuid.UUID,
    grant: PermissionGrant = Depends(require_permission("encuentros:gestionar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: EncuentroService = Depends(_get_service),
):
    """Genera bloque HTML con tabla de instancias para embeber en LMS."""
    try:
        html = await service.generate_html(
            tenant_id=current_user.tenant_id,
            slot_id=slot_id,
            actor_id=current_user.actor_id,
            is_global=grant.scope == "global",
            session=db,
        )
    except EncuentroError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    return HTMLResponse(content=html, status_code=200)

"""Router de calificaciones — importación, umbral, reporte y vaciado.

Endpoints:
  POST   /calificaciones/preview               — preview archivo (calificaciones:importar)
  POST   /calificaciones/confirmar              — confirmar importación (calificaciones:importar)
  POST   /calificaciones/reporte-finalizacion   — reporte entregas sin calificar (calificaciones:importar)
  GET    /calificaciones                        — listar calificaciones con aprobado (calificaciones:importar)
  GET    /calificaciones/umbral                 — obtener umbral (calificaciones:importar)
  PUT    /calificaciones/umbral                 — configurar umbral (calificaciones:configurar-umbral)
  POST   /calificaciones/vaciar                 — vaciar calificaciones (calificaciones:vaciar)
"""

from __future__ import annotations

import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import AuditCodes, AuditContext
from app.core.dependencies import get_current_user, get_db
from app.core.permissions import PermissionGrant, require_permission
from app.schemas.calificacion import (
    CalificacionResponse,
    ConfirmarImportRequest,
    PreviewResponse,
    ReporteFinalizacionResponse,
    UmbralMateriaCreate,
    UmbralMateriaResponse,
    VaciarRequest,
)
from app.services.calificacion_service import CalificacionError, CalificacionService, UmbralService

router = APIRouter(prefix="/api/v1/calificaciones", tags=["calificaciones"])


def _get_calificacion_service() -> CalificacionService:
    return CalificacionService()


def _get_umbral_service() -> UmbralService:
    return UmbralService()


def _build_audit_ctx(request: Request, current_user) -> AuditContext:
    return AuditContext(
        actor_id=current_user.actor_id,
        tenant_id=current_user.tenant_id,
        ip=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", ""),
        impersonado_id=current_user.id if getattr(current_user, "impersonated", False) else None,
    )


@router.post("/preview", response_model=PreviewResponse)
async def preview_calificaciones(
    file: UploadFile,
    grant: PermissionGrant = Depends(require_permission("calificaciones:importar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
    service: CalificacionService = Depends(_get_calificacion_service),
):
    """Previsualiza un archivo .csv de calificaciones."""
    contenido = await file.read()
    try:
        resultado = await service.preview_archivo(
            contenido=contenido,
            nombre_archivo=file.filename or "archivo.csv",
        )
    except CalificacionError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)
    return resultado


@router.post("/confirmar", status_code=201)
async def confirmar_importacion(
    body: ConfirmarImportRequest,
    grant: PermissionGrant = Depends(require_permission("calificaciones:importar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
    service: CalificacionService = Depends(_get_calificacion_service),
):
    """Confirma la importación de calificaciones desde un archivo previamente previsualizado.

    El body debe incluir ``archivo_parseado`` (filas), ``columnas_detectadas``
    y ``actividades_seleccionadas``.
    El request se envía como JSON con los datos parseados del preview.
    """
    audit_ctx = _build_audit_ctx(request, current_user)
    try:
        # El body se recibe como JSON genérico porque archivo_parseado y
        # columnas_detectadas son dinámicos
        total = await service.confirmar_importacion(
            tenant_id=current_user.tenant_id,
            materia_id=body.materia_id,
            archivo_parseado=getattr(body, "archivo_parseado", []),
            columnas_detectadas=getattr(body, "columnas_detectadas", []),
            actividades_seleccionadas=body.actividades_seleccionadas,
            actor_id=current_user.actor_id,
            audit_ctx=audit_ctx,
            session=db,
        )
    except CalificacionError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)
    return {"total_creadas": total}


@router.post("/reporte-finalizacion", response_model=ReporteFinalizacionResponse)
async def reporte_finalizacion(
    file: UploadFile,
    materia_id: str = Query(..., description="UUID de la materia"),
    grant: PermissionGrant = Depends(require_permission("calificaciones:importar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
    service: CalificacionService = Depends(_get_calificacion_service),
):
    """Genera reporte de entregas finalizadas sin calificar."""
    try:
        materia_uuid = UUID(materia_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="materia_id inválido")

    contenido = await file.read()
    try:
        resultado = await service.reporte_finalizacion(
            tenant_id=current_user.tenant_id,
            materia_id=materia_uuid,
            archivo_contenido=contenido,
            nombre_archivo=file.filename or "archivo.csv",
            session=db,
        )
    except CalificacionError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)
    return resultado


@router.get("", response_model=list[CalificacionResponse])
async def listar_calificaciones(
    materia_id: str = Query(..., description="UUID de la materia"),
    grant: PermissionGrant = Depends(require_permission("calificaciones:importar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: CalificacionService = Depends(_get_calificacion_service),
):
    """Lista calificaciones del usuario para una materia, con ``aprobado`` derivado."""
    try:
        materia_uuid = UUID(materia_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="materia_id inválido")

    try:
        resultado = await service.get_calificaciones(
            tenant_id=current_user.tenant_id,
            materia_id=materia_uuid,
            creado_por=current_user.actor_id,
            session=db,
        )
    except CalificacionError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)
    return resultado


@router.get("/umbral", response_model=UmbralMateriaResponse | None)
async def get_umbral(
    materia_id: str = Query(..., description="UUID de la materia"),
    grant: PermissionGrant = Depends(require_permission("calificaciones:importar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: UmbralService = Depends(_get_umbral_service),
):
    """Obtiene el umbral de aprobación para la materia del usuario."""
    # Buscar asignación del usuario para esta materia
    from app.models.asignacion import Asignacion
    from sqlalchemy import select

    try:
        materia_uuid = UUID(materia_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="materia_id inválido")

    try:
        stmt = select(Asignacion.id).where(
            Asignacion.tenant_id == current_user.tenant_id,
            Asignacion.usuario_id == current_user.actor_id,
            Asignacion.materia_id == materia_uuid,
            Asignacion.deleted_at.is_(None),
        ).limit(1)
        result = await db.execute(stmt)
        asignacion_id = result.scalar_one_or_none()

        if asignacion_id is None:
            return None

        umbral = await service.get_umbral(
            tenant_id=current_user.tenant_id,
            asignacion_id=asignacion_id,
            session=db,
        )
    except CalificacionError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)
    return umbral


@router.put("/umbral", response_model=UmbralMateriaResponse)
async def configurar_umbral(
    body: UmbralMateriaCreate,
    materia_id: str = Query(..., description="UUID de la materia"),
    grant: PermissionGrant = Depends(require_permission("calificaciones:configurar-umbral")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
    service: UmbralService = Depends(_get_umbral_service),
):
    """Configura el umbral de aprobación para una materia."""
    from app.models.asignacion import Asignacion
    from sqlalchemy import select

    try:
        materia_uuid = UUID(materia_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="materia_id inválido")

    # Buscar asignación del usuario
    try:
        stmt = select(Asignacion.id).where(
            Asignacion.tenant_id == current_user.tenant_id,
            Asignacion.usuario_id == current_user.actor_id,
            Asignacion.materia_id == materia_uuid,
            Asignacion.deleted_at.is_(None),
        ).limit(1)
        result = await db.execute(stmt)
        asignacion_id = result.scalar_one_or_none()

        if asignacion_id is None:
            raise HTTPException(status_code=404, detail="No tenés asignación a esta materia")

        audit_ctx = _build_audit_ctx(request, current_user)
        umbral = await service.configurar_umbral(
            tenant_id=current_user.tenant_id,
            asignacion_id=asignacion_id,
            materia_id=materia_uuid,
            umbral_pct=body.umbral_pct,
            valores_aprobatorios=body.valores_aprobatorios,
            audit_ctx=audit_ctx,
            session=db,
        )
    except CalificacionError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)
    return umbral


@router.post("/vaciar", status_code=204)
async def vaciar_calificaciones(
    body: VaciarRequest,
    grant: PermissionGrant = Depends(require_permission("calificaciones:vaciar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
    service: CalificacionService = Depends(_get_calificacion_service),
):
    """Vacía las calificaciones del usuario para una materia (soft-delete)."""
    audit_ctx = _build_audit_ctx(request, current_user)
    try:
        await service.vaciar_materia(
            tenant_id=current_user.tenant_id,
            materia_id=body.materia_id,
            actor_id=current_user.actor_id,
            audit_ctx=audit_ctx,
            session=db,
        )
    except CalificacionError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)
    return None

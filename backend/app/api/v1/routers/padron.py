from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import AuditCodes, AuditContext, audit_action
from app.core.dependencies import get_current_user, get_db
from app.core.permissions import PermissionGrant, require_permission
from app.schemas.padron import (
    ConfirmarRequest,
    ConfirmarResponse,
    MoodleSyncResponse,
    PreviewResponse,
    VaciarRequest,
    VersionPadronListResponse,
    VersionPadronResponse,
)
from app.services.padron_service import PadronError, PadronService

router = APIRouter(prefix="/api/v1/padron", tags=["padron"])


def _get_service() -> PadronService:
    return PadronService()


def _build_audit_ctx(request: Request, current_user) -> AuditContext:
    return AuditContext(
        actor_id=current_user.actor_id,
        tenant_id=current_user.tenant_id,
        ip=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", ""),
        impersonado_id=current_user.id if getattr(current_user, "impersonated", False) else None,
    )


@router.post("/preview", response_model=PreviewResponse)
async def preview_padron(
    file: UploadFile,
    grant: PermissionGrant = Depends(require_permission("padron:cargar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
    service: PadronService = Depends(_get_service),
):
    contenido = await file.read()
    try:
        resultado = await service.preview_archivo(
            contenido=contenido,
            nombre_archivo=file.filename or "archivo.csv",
        )
    except PadronError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)
    return resultado


@router.post("/confirmar", response_model=ConfirmarResponse, status_code=201)
async def confirmar_padron(
    body: ConfirmarRequest,
    grant: PermissionGrant = Depends(require_permission("padron:cargar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
    service: PadronService = Depends(_get_service),
):
    audit_ctx = _build_audit_ctx(request, current_user)
    try:
        resultado = await service.confirmar_carga(
            tenant_id=current_user.tenant_id,
            materia_id=body.materia_id,
            cohorte_id=body.cohorte_id,
            entradas=body.entradas,
            audit_ctx=audit_ctx,
            session=db,
            origen="archivo",
        )
    except PadronError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)
    return resultado


@router.post("/sync-moodle", response_model=MoodleSyncResponse, status_code=201)
async def sync_moodle_padron(
    body: dict,
    grant: PermissionGrant = Depends(require_permission("padron:cargar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
    service: PadronService = Depends(_get_service),
):
    materia_id = body.get("materia_id")
    cohorte_id = body.get("cohorte_id")
    if not materia_id or not cohorte_id:
        raise HTTPException(status_code=422, detail="materia_id and cohorte_id are required")
    from uuid import UUID
    try:
        materia_uuid = UUID(materia_id)
        cohorte_uuid = UUID(cohorte_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid UUID format")
    audit_ctx = _build_audit_ctx(request, current_user)
    try:
        resultado = await service.sync_moodle(
            tenant_id=current_user.tenant_id,
            materia_id=materia_uuid,
            cohorte_id=cohorte_uuid,
            audit_ctx=audit_ctx,
            session=db,
        )
    except PadronError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)
    return resultado


@router.delete("/vaciar", status_code=204)
async def vaciar_padron(
    body: VaciarRequest,
    grant: PermissionGrant = Depends(require_permission("padron:vaciar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
    service: PadronService = Depends(_get_service),
):
    audit_ctx = _build_audit_ctx(request, current_user)
    try:
        await service.vaciar_materia(
            tenant_id=current_user.tenant_id,
            materia_id=body.materia_id,
            actor_id=current_user.actor_id,
            scope_global=grant.scope == "global",
            audit_ctx=audit_ctx,
            session=db,
        )
    except PadronError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)
    return None


@router.get("/versiones", response_model=VersionPadronListResponse)
async def listar_versiones_padron(
    grant: PermissionGrant = Depends(require_permission("padron:cargar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: PadronService = Depends(_get_service),
    materia_id: str | None = None,
    cohorte_id: str | None = None,
):
    from uuid import UUID
    materia_uuid = UUID(materia_id) if materia_id else None
    cohorte_uuid = UUID(cohorte_id) if cohorte_id else None
    versiones = await service.list_versiones(
        tenant_id=current_user.tenant_id,
        session=db,
        materia_id=materia_uuid,
        cohorte_id=cohorte_uuid,
    )
    return VersionPadronListResponse(versiones=versiones, total=len(versiones))

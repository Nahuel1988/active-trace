"""Router equipos — operaciones de bloque sobre equipos docentes (C-08).

Opera sobre Asignacion agrupadas por tupla (materia_id, carrera_id, cohorte_id).
Protegido por permiso 'equipos:asignar' excepto 'mis-equipos'.
"""

from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.core.permissions import PermissionGrant, require_permission
from app.schemas.equipo import (
    AsignacionMasivaRequest,
    AsignacionMasivaResponse,
    AsignacionMasivaItem,
    ClonarEquipoRequest,
    ClonarEquipoResponse,
    EquipoResumen,
    MisEquiposResponse,
    AsignacionEquipoItem,
    VigenciaBloqueRequest,
    VigenciaBloqueResponse,
)
from app.services.equipo_service import EquipoService

router = APIRouter(
    prefix="/api/v1/equipos",
    tags=["equipos"],
)


def _get_service() -> EquipoService:
    return EquipoService()


def _get_client_info(request: Request) -> tuple[str, str]:
    """Extrae IP y user_agent del request."""
    ip = request.client.host if request.client else "0.0.0.0"
    user_agent = request.headers.get("user-agent", "")
    return ip, user_agent


@router.get("/mis-equipos", response_model=list[MisEquiposResponse])
async def mis_equipos(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: EquipoService = Depends(_get_service),
):
    """Retorna las asignaciones vigentes del usuario agrupadas por equipo.

    No requiere permiso 'equipos:asignar'. La identidad se toma del JWT.
    """
    grupos = await service.get_mis_equipos(
        tenant_id=current_user.tenant_id,
        usuario_id=current_user.id,
        session=db,
    )

    result = []
    for g in grupos:
        items = [AsignacionEquipoItem(**item) for item in g["asignaciones"]]
        result.append(MisEquiposResponse(
            materia_id=g["materia_id"],
            carrera_id=g["carrera_id"],
            cohorte_id=g["cohorte_id"],
            asignaciones=items,
        ))

    return result


@router.get("", response_model=list[EquipoResumen])
async def listar_equipos(
    materia_id: Optional[uuid.UUID] = Query(default=None),
    carrera_id: Optional[uuid.UUID] = Query(default=None),
    cohorte_id: Optional[uuid.UUID] = Query(default=None),
    grant: PermissionGrant = Depends(require_permission("equipos:asignar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: EquipoService = Depends(_get_service),
):
    """Lista equipos (tuplas distintas) con conteo de vigentes.

    Protegido por 'equipos:asignar'.
    """
    rows = await service._repo.list_distinct_equipos(
        tenant_id=current_user.tenant_id,
        session=db,
        materia_id=materia_id,
        carrera_id=carrera_id,
        cohorte_id=cohorte_id,
    )
    return [EquipoResumen(**r) for r in rows]


@router.post("/asignacion-masiva", response_model=AsignacionMasivaResponse, status_code=201)
async def asignacion_masiva(
    body: AsignacionMasivaRequest,
    request: Request,
    grant: PermissionGrant = Depends(require_permission("equipos:asignar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: EquipoService = Depends(_get_service),
):
    """Asignación masiva best-effort.

    Crea asignaciones para múltiples usuarios en el mismo contexto.
    Las válidas se crean; las inválidas se reportan.
    Protegido por 'equipos:asignar'.
    """
    from app.models.role import Role
    from sqlalchemy import select

    try:
        role_uuid = uuid.UUID(body.role_id)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"role_id '{body.role_id}' is not a valid UUID")

    stmt = select(Role).where(
        Role.id == role_uuid,
        Role.tenant_id == current_user.tenant_id,
        Role.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    role = result.scalar_one_or_none()
    if role is None:
        raise HTTPException(status_code=404, detail="role not found")

    ip, user_agent = _get_client_info(request)

    try:
        usuario_uuids = [uuid.UUID(uid) for uid in body.usuario_ids]
    except ValueError:
        raise HTTPException(status_code=422, detail="One or more usuario_ids are not valid UUIDs")

    def _parse_uuid(value: str | None, name: str) -> uuid.UUID | None:
        if value is None:
            return None
        try:
            return uuid.UUID(value)
        except ValueError:
            raise HTTPException(status_code=422, detail=f"'{name}' is not a valid UUID: {value}")

    materia_uuid = _parse_uuid(body.materia_id, "materia_id")
    carrera_uuid = _parse_uuid(body.carrera_id, "carrera_id")
    cohorte_uuid = _parse_uuid(body.cohorte_id, "cohorte_id")
    responsable_uuid = _parse_uuid(body.responsable_id, "responsable_id")

    resumen = await service.asignacion_masiva(
        tenant_id=current_user.tenant_id,
        actor_id=current_user.id,
        role_id=role_uuid,
        role_code=role.code,
        usuario_ids=usuario_uuids,
        materia_id=materia_uuid,
        carrera_id=carrera_uuid,
        cohorte_id=cohorte_uuid,
        comisiones=body.comisiones,
        responsable_id=responsable_uuid,
        desde=body.desde,
        hasta=body.hasta,
        session=db,
        ip=ip,
        user_agent=user_agent,
    )

    return AsignacionMasivaResponse(
        creadas=resumen["creadas"],
        rechazadas=[AsignacionMasivaItem(**r) for r in resumen["rechazadas"]],
        omitidas=[AsignacionMasivaItem(**r) for r in resumen["omitidas"]],
    )


@router.post("/clonar", response_model=ClonarEquipoResponse, status_code=201)
async def clonar_equipo(
    body: ClonarEquipoRequest,
    request: Request,
    grant: PermissionGrant = Depends(require_permission("equipos:asignar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: EquipoService = Depends(_get_service),
):
    """Clona asignaciones de un equipo origen a uno destino.

    Solo copia vigentes. Reescribe carrera/cohorte/vigencia.
    Protegido por 'equipos:asignar'.
    """
    ip, user_agent = _get_client_info(request)

    resumen = await service.clonar_equipo(
        tenant_id=current_user.tenant_id,
        actor_id=current_user.id,
        origen_materia_id=uuid.UUID(body.origen_materia_id),
        origen_carrera_id=uuid.UUID(body.origen_carrera_id),
        origen_cohorte_id=uuid.UUID(body.origen_cohorte_id),
        destino_carrera_id=uuid.UUID(body.destino_carrera_id),
        destino_cohorte_id=uuid.UUID(body.destino_cohorte_id),
        destino_materia_id=uuid.UUID(body.destino_materia_id) if body.destino_materia_id else None,
        nuevo_desde=body.nuevo_desde,
        nuevo_hasta=body.nuevo_hasta,
        session=db,
        ip=ip,
        user_agent=user_agent,
    )

    return ClonarEquipoResponse(
        clonadas=resumen["clonadas"],
        omitidas=[AsignacionMasivaItem(**r) for r in resumen["omitidas"]],
    )


@router.patch("/vigencia", response_model=VigenciaBloqueResponse)
async def modificar_vigencia(
    body: VigenciaBloqueRequest,
    request: Request,
    grant: PermissionGrant = Depends(require_permission("equipos:asignar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: EquipoService = Depends(_get_service),
):
    """Actualiza vigencia de todas las asignaciones de un equipo.

    Todo-o-nada. Valida desde ≤ hasta.
    Protegido por 'equipos:asignar'.
    """
    ip, user_agent = _get_client_info(request)

    try:
        resumen = await service.modificar_vigencia_bloque(
            tenant_id=current_user.tenant_id,
            actor_id=current_user.id,
            materia_id=uuid.UUID(body.materia_id) if body.materia_id else None,
            carrera_id=uuid.UUID(body.carrera_id) if body.carrera_id else None,
            cohorte_id=uuid.UUID(body.cohorte_id) if body.cohorte_id else None,
            desde=body.desde,
            hasta=body.hasta,
            session=db,
            ip=ip,
            user_agent=user_agent,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return VigenciaBloqueResponse(filas_afectadas=resumen["filas_afectadas"])


@router.get("/export")
async def export_equipo_csv(
    materia_id: Optional[uuid.UUID] = Query(default=None),
    carrera_id: Optional[uuid.UUID] = Query(default=None),
    cohorte_id: Optional[uuid.UUID] = Query(default=None),
    grant: PermissionGrant = Depends(require_permission("equipos:asignar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: EquipoService = Depends(_get_service),
):
    """Exporta asignaciones del equipo a CSV.

    Protegido por 'equipos:asignar'.
    """
    from fastapi.responses import PlainTextResponse

    csv_content = await service.export_equipo_csv(
        tenant_id=current_user.tenant_id,
        materia_id=materia_id,
        carrera_id=carrera_id,
        cohorte_id=cohorte_id,
        session=db,
    )

    return PlainTextResponse(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=equipo.csv"},
    )

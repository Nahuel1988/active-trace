import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.core.permissions import PermissionGrant, require_permission
from app.schemas.evaluacion import (
    CandidatosImportRequest,
    CandidatosImportResponse,
    CandidatoRechazado,
    EvaluacionConMetricas,
    EvaluacionCreate,
    EvaluacionResponse,
    EvaluacionUpdate,
    MetricasPanel,
    AgendaItem,
    MisReservasItem,
    ReservaCreate,
    ReservaResponse,
    RegistroAcademicoItem,
    ResultadoConAlumno,
    ResultadoCreate,
    ResultadoResponse,
    ResultadoUpdate,
)
from app.services.evaluacion_service import EvaluacionService, EvaluacionServiceError
from app.services.reserva_service import ReservaService, ReservaServiceError
from app.services.resultado_service import ResultadoService, ResultadoServiceError

router = APIRouter(
    prefix="/api/v1/coloquios",
    tags=["coloquios"],
)


def _get_evaluacion_service() -> EvaluacionService:
    return EvaluacionService()


def _get_reserva_service() -> ReservaService:
    return ReservaService()


def _get_resultado_service() -> ResultadoService:
    return ResultadoService()


# ── Convocatorias (coloquios:gestionar) ─────────────────────────────────────


@router.get("", response_model=list[EvaluacionConMetricas])
async def listar_coloquios(
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0),
    grant: PermissionGrant = Depends(require_permission("coloquios:gestionar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: EvaluacionService = Depends(_get_evaluacion_service),
):
    return await service.list(
        tenant_id=current_user.tenant_id, session=db, limit=limit, offset=offset
    )


@router.post("", response_model=EvaluacionResponse, status_code=201)
async def crear_coloquio(
    body: EvaluacionCreate,
    grant: PermissionGrant = Depends(require_permission("coloquios:gestionar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: EvaluacionService = Depends(_get_evaluacion_service),
):
    try:
        evaluacion = await service.create(
            tenant_id=current_user.tenant_id,
            materia_id=body.materia_id,
            cohorte_id=body.cohorte_id,
            tipo=body.tipo,
            instancia=body.instancia,
            dias_disponibles=body.dias_disponibles,
            session=db,
        )
    except EvaluacionServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    return EvaluacionResponse(
        id=evaluacion.id,
        tenant_id=evaluacion.tenant_id,
        materia_id=evaluacion.materia_id,
        cohorte_id=evaluacion.cohorte_id,
        tipo=evaluacion.tipo,
        instancia=evaluacion.instancia,
        dias_disponibles=evaluacion.dias_disponibles,
        created_at=evaluacion.created_at,
        updated_at=evaluacion.updated_at,
    )


@router.get("/{id}", response_model=EvaluacionConMetricas)
async def obtener_coloquio(
    id: uuid.UUID,
    grant: PermissionGrant = Depends(require_permission("coloquios:gestionar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: EvaluacionService = Depends(_get_evaluacion_service),
):
    try:
        result = await service.get(
            tenant_id=current_user.tenant_id, id=id, session=db
        )
    except EvaluacionServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    return EvaluacionConMetricas(**result)


@router.patch("/{id}", response_model=EvaluacionResponse)
async def actualizar_coloquio(
    id: uuid.UUID,
    body: EvaluacionUpdate,
    grant: PermissionGrant = Depends(require_permission("coloquios:gestionar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: EvaluacionService = Depends(_get_evaluacion_service),
):
    data = body.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status_code=400, detail="No fields to update")
    try:
        evaluacion = await service.update(
            tenant_id=current_user.tenant_id,
            id=id,
            data=data,
            session=db,
        )
    except EvaluacionServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    return EvaluacionResponse(
        id=evaluacion.id,
        tenant_id=evaluacion.tenant_id,
        materia_id=evaluacion.materia_id,
        cohorte_id=evaluacion.cohorte_id,
        tipo=evaluacion.tipo,
        instancia=evaluacion.instancia,
        dias_disponibles=evaluacion.dias_disponibles,
        created_at=evaluacion.created_at,
        updated_at=evaluacion.updated_at,
    )


@router.delete("/{id}", status_code=204)
async def eliminar_coloquio(
    id: uuid.UUID,
    grant: PermissionGrant = Depends(require_permission("coloquios:gestionar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: EvaluacionService = Depends(_get_evaluacion_service),
):
    try:
        await service.soft_delete(
            tenant_id=current_user.tenant_id, id=id, session=db
        )
    except EvaluacionServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@router.post("/{id}/candidatos", response_model=CandidatosImportResponse)
async def importar_candidatos(
    id: uuid.UUID,
    body: CandidatosImportRequest,
    grant: PermissionGrant = Depends(require_permission("coloquios:gestionar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: EvaluacionService = Depends(_get_evaluacion_service),
):
    try:
        result = await service.import_candidatos(
            tenant_id=current_user.tenant_id,
            evaluacion_id=id,
            usuario_ids=body.usuario_ids,
            session=db,
        )
    except EvaluacionServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    return CandidatosImportResponse(**result)


@router.get("/metricas", response_model=MetricasPanel)
async def metricas_panel(
    grant: PermissionGrant = Depends(require_permission("coloquios:gestionar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: EvaluacionService = Depends(_get_evaluacion_service),
):
    return await service.get_metricas_panel(tenant_id=current_user.tenant_id, session=db)


@router.get("/agenda", response_model=list[AgendaItem])
async def agenda_consolidada(
    materia_id: Optional[uuid.UUID] = Query(default=None),
    cohorte_id: Optional[uuid.UUID] = Query(default=None),
    evaluacion_id: Optional[uuid.UUID] = Query(default=None),
    fecha_desde: Optional[datetime] = Query(default=None),
    fecha_hasta: Optional[datetime] = Query(default=None),
    grant: PermissionGrant = Depends(require_permission("coloquios:gestionar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: EvaluacionService = Depends(_get_evaluacion_service),
):
    return await service.get_agenda(
        tenant_id=current_user.tenant_id,
        session=db,
        materia_id=materia_id,
        cohorte_id=cohorte_id,
        evaluacion_id=evaluacion_id,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
    )


# ── Reservas (coloquios:reservar) ───────────────────────────────────────────


@router.post("/{id}/reservas", response_model=ReservaResponse, status_code=201)
async def crear_reserva(
    id: uuid.UUID,
    body: ReservaCreate,
    grant: PermissionGrant = Depends(require_permission("coloquios:reservar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: ReservaService = Depends(_get_reserva_service),
):
    try:
        result = await service.crear_reserva(
            tenant_id=current_user.tenant_id,
            evaluacion_id=id,
            alumno_id=current_user.id,
            fecha_hora=body.fecha_hora,
            session=db,
        )
    except ReservaServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    return ReservaResponse(**result)


@router.patch("/{id}/reservas/{reserva_id}/cancelar", response_model=dict)
async def cancelar_reserva(
    id: uuid.UUID,
    reserva_id: uuid.UUID,
    grant: PermissionGrant = Depends(require_permission("coloquios:reservar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: ReservaService = Depends(_get_reserva_service),
):
    # Check if user also has coloquios:gestionar
    from app.services.permission_service import PermissionService

    perm_service = PermissionService()
    gestionar_grant = await perm_service.verify_permission(
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        required_code="coloquios:gestionar",
        session=db,
    )
    has_gestionar = gestionar_grant is not None

    try:
        result = await service.cancelar_reserva(
            tenant_id=current_user.tenant_id,
            evaluacion_id=id,
            reserva_id=reserva_id,
            alumno_id=current_user.id,
            has_gestionar=has_gestionar,
            session=db,
        )
    except ReservaServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    return result


@router.get("/mis-reservas", response_model=list[MisReservasItem])
async def mis_reservas(
    estado: Optional[str] = Query(default=None, pattern="^(Activa|Cancelada)?$"),
    grant: PermissionGrant = Depends(require_permission("coloquios:reservar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: ReservaService = Depends(_get_reserva_service),
):
    return await service.get_mis_reservas(
        alumno_id=current_user.id,
        tenant_id=current_user.tenant_id,
        session=db,
        estado=estado,
    )


# ── Resultados (coloquios:gestionar) ────────────────────────────────────────


@router.post("/{id}/resultados", response_model=ResultadoResponse, status_code=201)
async def registrar_resultado(
    id: uuid.UUID,
    body: ResultadoCreate,
    grant: PermissionGrant = Depends(require_permission("coloquios:gestionar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: ResultadoService = Depends(_get_resultado_service),
):
    try:
        resultado = await service.registrar(
            tenant_id=current_user.tenant_id,
            evaluacion_id=id,
            alumno_id=body.alumno_id,
            nota_final=body.nota_final,
            actor_id=current_user.actor_id,
            session=db,
        )
    except ResultadoServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    return ResultadoResponse(
        id=resultado.id,
        tenant_id=resultado.tenant_id,
        evaluacion_id=resultado.evaluacion_id,
        alumno_id=resultado.alumno_id,
        nota_final=resultado.nota_final,
        created_at=resultado.created_at,
        updated_at=resultado.updated_at,
    )


@router.patch("/{id}/resultados/{resultado_id}", response_model=ResultadoResponse)
async def actualizar_resultado(
    id: uuid.UUID,
    resultado_id: uuid.UUID,
    body: ResultadoUpdate,
    grant: PermissionGrant = Depends(require_permission("coloquios:gestionar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: ResultadoService = Depends(_get_resultado_service),
):
    try:
        resultado = await service.actualizar(
            tenant_id=current_user.tenant_id,
            evaluacion_id=id,
            resultado_id=resultado_id,
            nota_final=body.nota_final,
            actor_id=current_user.actor_id,
            session=db,
        )
    except ResultadoServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    return ResultadoResponse(
        id=resultado.id,
        tenant_id=resultado.tenant_id,
        evaluacion_id=resultado.evaluacion_id,
        alumno_id=resultado.alumno_id,
        nota_final=resultado.nota_final,
        created_at=resultado.created_at,
        updated_at=resultado.updated_at,
    )


@router.get("/{id}/resultados", response_model=list[ResultadoConAlumno])
async def listar_resultados(
    id: uuid.UUID,
    grant: PermissionGrant = Depends(require_permission("coloquios:gestionar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: ResultadoService = Depends(_get_resultado_service),
):
    try:
        return await service.listar_por_evaluacion(
            evaluacion_id=id, tenant_id=current_user.tenant_id, session=db
        )
    except ResultadoServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@router.get("/registro-academico", response_model=list[RegistroAcademicoItem])
async def registro_academico(
    materia_id: Optional[uuid.UUID] = Query(default=None),
    cohorte_id: Optional[uuid.UUID] = Query(default=None),
    alumno_id: Optional[uuid.UUID] = Query(default=None),
    grant: PermissionGrant = Depends(require_permission("coloquios:gestionar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: ResultadoService = Depends(_get_resultado_service),
):
    return await service.get_registro_academico(
        tenant_id=current_user.tenant_id,
        session=db,
        materia_id=materia_id,
        cohorte_id=cohorte_id,
        alumno_id=alumno_id,
    )


@router.get("/mi-registro", response_model=list[RegistroAcademicoItem])
async def mi_registro(
    grant: PermissionGrant = Depends(require_permission("coloquios:reservar")),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: ResultadoService = Depends(_get_resultado_service),
):
    return await service.get_registro_academico(
        tenant_id=current_user.tenant_id,
        session=db,
        alumno_id=current_user.id,
    )

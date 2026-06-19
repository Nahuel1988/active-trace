"""Router de inbox (mensajería interna) — C-20.

Endpoints:
    GET  /api/v1/inbox                    — lista hilos del inbox del usuario
    GET  /api/v1/inbox/{hilo_id}          — abre un hilo (marca leídos)
    POST /api/v1/inbox                    — inicia un hilo nuevo
    POST /api/v1/inbox/{hilo_id}/responder — responde en un hilo existente

Sin lógica de negocio — delega totalmente a MensajeriaService.
Identidad SIEMPRE del JWT (get_current_user), nunca del body.
Fail-closed: no-participante recibe 403 (nunca 404 que filtraría existencia).
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.repositories.hilo_mensaje_repository import HiloMensajeRepository
from app.repositories.mensaje_interno_repository import MensajeInternoRepository
from app.repositories.usuario_repository import UsuarioRepository
from app.schemas.inbox import (
    HiloListItem,
    HiloRead,
    IniciarHilo,
    MensajeRead,
    ResponderMensaje,
)
from app.services.mensajeria_service import MensajeriaService

router = APIRouter(
    prefix="/api/v1/inbox",
    tags=["inbox"],
)


def _get_service() -> MensajeriaService:
    return MensajeriaService(
        hilo_repo=HiloMensajeRepository(),
        mensaje_repo=MensajeInternoRepository(),
        usuario_repo=UsuarioRepository(),
    )


@router.get("", response_model=list[HiloListItem])
async def listar_inbox(
    limit: int = 50,
    offset: int = 0,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: MensajeriaService = Depends(_get_service),
) -> list[HiloListItem]:
    """Lista los hilos del inbox del usuario autenticado.

    Solo aparecen hilos donde el caller es participante.
    Ordenados por actividad reciente.
    """
    hilos = await service.listar_inbox(
        tenant_id=current_user.tenant_id,
        current_user_id=current_user.id,
        session=db,
        limit=limit,
        offset=offset,
    )
    result = []
    for h in hilos:
        # Contraparte = el otro participante
        contraparte_id = (
            str(h.destinatario_id)
            if h.iniciado_por == current_user.id
            else str(h.iniciado_por)
        )
        result.append(
            HiloListItem(
                id=str(h.id),
                asunto=h.asunto,
                contraparte_id=contraparte_id,
                tiene_no_leidos=False,  # simplificado: sin denormalizar contador
                ultimo_mensaje_at=h.updated_at,
            )
        )
    return result


@router.get("/{hilo_id}", response_model=HiloRead)
async def abrir_hilo(
    hilo_id: uuid.UUID,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: MensajeriaService = Depends(_get_service),
) -> HiloRead:
    """Abre un hilo y marca los mensajes como leídos.

    403 si el caller no es participante (fail-closed, nunca 404).
    """
    hilo, mensajes = await service.abrir_hilo(
        tenant_id=current_user.tenant_id,
        current_user_id=current_user.id,
        hilo_id=hilo_id,
        session=db,
    )
    return HiloRead(
        id=str(hilo.id),
        tenant_id=str(hilo.tenant_id),
        asunto=hilo.asunto,
        iniciado_por=str(hilo.iniciado_por),
        destinatario_id=str(hilo.destinatario_id),
        mensajes=[
            MensajeRead(
                id=str(m.id),
                hilo_id=str(m.hilo_id),
                autor_id=str(m.autor_id),
                cuerpo=m.cuerpo,
                creado_at=m.creado_at,
                leido_at=m.leido_at,
            )
            for m in mensajes
        ],
        created_at=hilo.created_at,
    )


@router.post("", response_model=HiloRead, status_code=201)
async def iniciar_hilo(
    body: IniciarHilo,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: MensajeriaService = Depends(_get_service),
) -> HiloRead:
    """Inicia un hilo nuevo hacia otro usuario del tenant.

    El remitente SIEMPRE es el usuario del JWT, nunca del body.
    El destinatario se valida: debe existir, activo, mismo tenant.
    """
    hilo, msg = await service.iniciar_hilo(
        tenant_id=current_user.tenant_id,
        current_user_id=current_user.id,
        destinatario_id=body.destinatario_id,
        asunto=body.asunto,
        cuerpo=body.cuerpo,
        session=db,
    )
    return HiloRead(
        id=str(hilo.id),
        tenant_id=str(hilo.tenant_id),
        asunto=hilo.asunto,
        iniciado_por=str(hilo.iniciado_por),
        destinatario_id=str(hilo.destinatario_id),
        mensajes=[
            MensajeRead(
                id=str(msg.id),
                hilo_id=str(msg.hilo_id),
                autor_id=str(msg.autor_id),
                cuerpo=msg.cuerpo,
                creado_at=msg.creado_at,
                leido_at=msg.leido_at,
            )
        ],
        created_at=hilo.created_at,
    )


@router.post("/{hilo_id}/responder", response_model=MensajeRead, status_code=201)
async def responder_hilo(
    hilo_id: uuid.UUID,
    body: ResponderMensaje,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: MensajeriaService = Depends(_get_service),
) -> MensajeRead:
    """Agrega una respuesta a un hilo existente.

    403 si el caller no es participante (fail-closed).
    El autor SIEMPRE es el usuario del JWT, nunca del body.
    """
    msg = await service.responder(
        tenant_id=current_user.tenant_id,
        current_user_id=current_user.id,
        hilo_id=hilo_id,
        cuerpo=body.cuerpo,
        session=db,
    )
    return MensajeRead(
        id=str(msg.id),
        hilo_id=str(msg.hilo_id),
        autor_id=str(msg.autor_id),
        cuerpo=msg.cuerpo,
        creado_at=msg.creado_at,
        leido_at=msg.leido_at,
    )

"""MensajeriaService — lógica de negocio para mensajería interna (C-20).

Reglas:
    - Remitente/autor SIEMPRE del JWT (current_user_id param), nunca del body.
    - Destinatario validado: debe existir, estar activo, mismo tenant.
    - Fail-closed: no-participante → 403 (no 404, para no filtrar existencia).
    - Aislamiento por tenant y por participante en todas las operaciones.
    - Al abrir un hilo: se marcan leídos los mensajes dirigidos al caller.
"""

from __future__ import annotations

import uuid
from typing import List, Tuple

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.hilo_mensaje import HiloMensaje
from app.models.mensaje_interno import MensajeInterno
from app.repositories.hilo_mensaje_repository import HiloMensajeRepository
from app.repositories.mensaje_interno_repository import MensajeInternoRepository
from app.repositories.usuario_repository import UsuarioRepository


class MensajeriaService:
    """Servicio para gestionar el inbox de mensajería interna entre usuarios."""

    def __init__(
        self,
        hilo_repo: HiloMensajeRepository,
        mensaje_repo: MensajeInternoRepository,
        usuario_repo: UsuarioRepository,
    ) -> None:
        self._hilos = hilo_repo
        self._mensajes = mensaje_repo
        self._usuarios = usuario_repo

    async def listar_inbox(
        self,
        *,
        tenant_id: uuid.UUID,
        current_user_id: uuid.UUID,
        session: AsyncSession,
        limit: int = 50,
        offset: int = 0,
    ) -> List[HiloMensaje]:
        """Lista los hilos donde el usuario de la sesión participa.

        Args:
            tenant_id: Tenant de la sesión.
            current_user_id: UUID del usuario (del JWT).
            session: Sesión async.
            limit: Tamaño de página.
            offset: Inicio de página.

        Returns:
            Lista de hilos del usuario.
        """
        return await self._hilos.listar_hilos_de(
            tenant_id=tenant_id,
            user_id=current_user_id,
            session=session,
            limit=limit,
            offset=offset,
        )

    async def abrir_hilo(
        self,
        *,
        tenant_id: uuid.UUID,
        current_user_id: uuid.UUID,
        hilo_id: uuid.UUID,
        session: AsyncSession,
    ) -> Tuple[HiloMensaje, List[MensajeInterno]]:
        """Abre un hilo y marca los mensajes dirigidos al caller como leídos.

        Fail-closed: si el caller no es participante → 403.

        Args:
            tenant_id: Tenant de la sesión.
            current_user_id: UUID del usuario (del JWT).
            hilo_id: UUID del hilo a abrir.
            session: Sesión async.

        Returns:
            Tupla (HiloMensaje, lista de MensajeInterno ordenados).

        Raises:
            HTTPException 403: Si el caller no es participante del hilo.
        """
        hilo = await self._hilos.get_para_participante(
            tenant_id=tenant_id,
            hilo_id=hilo_id,
            user_id=current_user_id,
            session=session,
        )
        if hilo is None:
            raise HTTPException(status_code=403, detail="No sos participante de este hilo")

        # Marcar leídos los mensajes que le llegaron al caller
        await self._mensajes.marcar_leidos(
            tenant_id=tenant_id,
            hilo_id=hilo_id,
            destinatario_id=current_user_id,
            session=session,
        )

        mensajes = await self._mensajes.listar_mensajes(
            tenant_id=tenant_id, hilo_id=hilo_id, session=session
        )
        return hilo, mensajes

    async def iniciar_hilo(
        self,
        *,
        tenant_id: uuid.UUID,
        current_user_id: uuid.UUID,
        destinatario_id: uuid.UUID,
        asunto: str,
        cuerpo: str,
        session: AsyncSession,
    ) -> Tuple[HiloMensaje, MensajeInterno]:
        """Crea un hilo nuevo con su primer mensaje.

        El remitente SIEMPRE es current_user_id (del JWT).
        El destinatario se valida: debe existir, activo, mismo tenant.

        Args:
            tenant_id: Tenant de la sesión.
            current_user_id: UUID del iniciador (del JWT).
            destinatario_id: UUID del destinatario (validado aquí).
            asunto: Asunto del hilo.
            cuerpo: Primer mensaje.
            session: Sesión async.

        Returns:
            Tupla (HiloMensaje, MensajeInterno creados).

        Raises:
            HTTPException 404: Si el destinatario no existe en el tenant o está inactivo.
        """
        # Validar destinatario: mismo tenant, activo
        destinatario = await self._usuarios.get(
            id=destinatario_id, tenant_id=tenant_id, session=session
        )
        if destinatario is None or not destinatario.is_active:
            raise HTTPException(
                status_code=404,
                detail="Destinatario no encontrado en este tenant",
            )

        hilo = await self._hilos.create_hilo(
            tenant_id=tenant_id,
            iniciado_por=current_user_id,
            destinatario_id=destinatario_id,
            asunto=asunto,
            session=session,
        )
        msg = await self._mensajes.agregar_mensaje(
            tenant_id=tenant_id,
            hilo_id=hilo.id,
            autor_id=current_user_id,
            cuerpo=cuerpo,
            session=session,
        )
        return hilo, msg

    async def responder(
        self,
        *,
        tenant_id: uuid.UUID,
        current_user_id: uuid.UUID,
        hilo_id: uuid.UUID,
        cuerpo: str,
        session: AsyncSession,
    ) -> MensajeInterno:
        """Agrega una respuesta a un hilo existente.

        Fail-closed: si el caller no es participante → 403.
        El autor SIEMPRE es current_user_id (del JWT).

        Args:
            tenant_id: Tenant de la sesión.
            current_user_id: UUID del autor (del JWT).
            hilo_id: UUID del hilo.
            cuerpo: Texto de la respuesta.
            session: Sesión async.

        Returns:
            MensajeInterno creado.

        Raises:
            HTTPException 403: Si el caller no es participante del hilo.
        """
        hilo = await self._hilos.get_para_participante(
            tenant_id=tenant_id,
            hilo_id=hilo_id,
            user_id=current_user_id,
            session=session,
        )
        if hilo is None:
            raise HTTPException(status_code=403, detail="No sos participante de este hilo")

        return await self._mensajes.agregar_mensaje(
            tenant_id=tenant_id,
            hilo_id=hilo_id,
            autor_id=current_user_id,
            cuerpo=cuerpo,
            session=session,
        )

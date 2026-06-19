"""Schemas Pydantic para el módulo de Mensajería Interna (Inbox) — C-20.

Shapes:
- HiloListItem: un hilo en el listado del inbox.
- HiloRead: detalle del hilo con sus mensajes.
- MensajeRead: un mensaje dentro de un hilo.
- IniciarHilo: body para POST /api/inbox. SIN autor_id/remitente_id.
- ResponderMensaje: body para POST /api/inbox/{id}/responder. SIN autor_id.

Todos con extra='forbid'.
El remitente/autor SIEMPRE se extrae del JWT en el service/router,
nunca del body del request.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class IniciarHilo(BaseModel):
    """Body para iniciar un hilo nuevo hacia otro usuario del tenant.

    El remitente (iniciado_por) SIEMPRE es current_user del JWT.
    NO declarar autor_id ni remitente_id aquí — con extra='forbid' → 422.
    """

    model_config = ConfigDict(extra="forbid")

    destinatario_id: uuid.UUID = Field(description="UUID del usuario destinatario (mismo tenant)")
    asunto: str = Field(description="Asunto o título de la conversación")
    cuerpo: str = Field(description="Cuerpo del primer mensaje del hilo")


class ResponderMensaje(BaseModel):
    """Body para agregar un mensaje a un hilo existente.

    El autor SIEMPRE es current_user del JWT.
    NO declarar autor_id aquí — con extra='forbid' → 422.
    """

    model_config = ConfigDict(extra="forbid")

    cuerpo: str = Field(description="Cuerpo de la respuesta")


class MensajeRead(BaseModel):
    """Representación de un mensaje dentro de un hilo."""

    model_config = ConfigDict(extra="forbid")

    id: str
    hilo_id: str
    autor_id: str
    cuerpo: str
    creado_at: datetime
    leido_at: Optional[datetime] = None


class HiloRead(BaseModel):
    """Detalle completo de un hilo con sus mensajes."""

    model_config = ConfigDict(extra="forbid")

    id: str
    tenant_id: str
    asunto: str
    iniciado_por: str
    destinatario_id: str
    mensajes: list[MensajeRead]
    created_at: datetime


class HiloListItem(BaseModel):
    """Un hilo en el listado del inbox."""

    model_config = ConfigDict(extra="forbid")

    id: str
    asunto: str
    contraparte_id: str
    tiene_no_leidos: bool
    ultimo_mensaje_at: Optional[datetime] = None

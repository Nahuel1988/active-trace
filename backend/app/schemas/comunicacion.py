from __future__ import annotations

import datetime
import uuid
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.comunicacion import EstadoComunicacion


class ComunicacionResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    enviado_por: uuid.UUID
    materia_id: Optional[uuid.UUID] = None
    destinatario: str
    destinatario_hash: str
    asunto: str
    cuerpo: str
    estado: EstadoComunicacion
    lote_id: Optional[uuid.UUID] = None
    requiere_aprobacion: bool
    enviado_at: Optional[datetime.datetime] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class DestinatarioPreview(BaseModel):
    email: str
    variables: dict[str, str]

    model_config = ConfigDict(extra="forbid")


class PreviewRequest(BaseModel):
    asunto_template: str
    cuerpo_template: str
    destinatarios: list[DestinatarioPreview]

    model_config = ConfigDict(extra="forbid")


class PreviewItem(BaseModel):
    destinatario: str
    asunto_render: str
    cuerpo_render: str

    model_config = ConfigDict(extra="forbid")


class PreviewResponse(BaseModel):
    items: list[PreviewItem]

    model_config = ConfigDict(extra="forbid")


class DestinatarioEnvio(BaseModel):
    email: str
    variables: dict[str, str]

    model_config = ConfigDict(extra="forbid")


class ComunicacionCreate(BaseModel):
    asunto_template: str
    cuerpo_template: str
    destinatarios: list[DestinatarioEnvio]
    materia_id: Optional[uuid.UUID] = None
    requiere_aprobacion: Optional[bool] = None

    model_config = ConfigDict(extra="forbid")


class LoteResumen(BaseModel):
    total: int = 0
    pendientes: int = 0
    enviando: int = 0
    enviadas: int = 0
    error: int = 0
    canceladas: int = 0

    model_config = ConfigDict(extra="forbid")


class LoteResponse(BaseModel):
    lote_id: uuid.UUID
    items: list[ComunicacionResponse]
    resumen: LoteResumen

    model_config = ConfigDict(extra="forbid")


class LoteActionResponse(BaseModel):
    lote_id: uuid.UUID
    afectados: int

    model_config = ConfigDict(extra="forbid")


class ComunicacionFiltros(BaseModel):
    estado: Optional[EstadoComunicacion] = None
    lote_id: Optional[uuid.UUID] = None
    materia_id: Optional[uuid.UUID] = None
    enviado_por: Optional[uuid.UUID] = None
    desde: Optional[datetime.datetime] = None
    hasta: Optional[datetime.datetime] = None

    model_config = ConfigDict(extra="forbid")

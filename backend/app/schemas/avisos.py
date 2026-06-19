from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class AvisoCreate(BaseModel):
    titulo: str
    cuerpo: str
    alcance: str
    severidad: str
    inicio_en: datetime
    fin_en: datetime
    materia_id: Optional[str] = None
    cohorte_id: Optional[str] = None
    rol_destino: Optional[str] = None
    orden: Optional[int] = None
    requiere_ack: Optional[bool] = None

    model_config = ConfigDict(extra='forbid')


class AvisoUpdate(BaseModel):
    titulo: Optional[str] = None
    cuerpo: Optional[str] = None
    alcance: Optional[str] = None
    severidad: Optional[str] = None
    inicio_en: Optional[datetime] = None
    fin_en: Optional[datetime] = None
    materia_id: Optional[str] = None
    cohorte_id: Optional[str] = None
    rol_destino: Optional[str] = None
    orden: Optional[int] = None
    activo: Optional[bool] = None
    requiere_ack: Optional[bool] = None

    model_config = ConfigDict(extra='forbid')


class AvisoResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    alcance: str
    materia_id: Optional[str] = None
    cohorte_id: Optional[str] = None
    rol_destino: Optional[str] = None
    severidad: str
    titulo: str
    cuerpo: str
    inicio_en: datetime
    fin_en: datetime
    orden: int
    activo: bool
    requiere_ack: bool
    created_at: datetime
    updated_at: datetime
    total_acks: int = 0
    total_visibles: int = 0

    model_config = ConfigDict(from_attributes=True)


class AvisoVisibleResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    alcance: str
    materia_id: Optional[str] = None
    cohorte_id: Optional[str] = None
    rol_destino: Optional[str] = None
    severidad: str
    titulo: str
    cuerpo: str
    inicio_en: datetime
    fin_en: datetime
    orden: int
    requiere_ack: bool
    acknowledged: bool = False

    model_config = ConfigDict(from_attributes=True)


class AckResponse(BaseModel):
    id: uuid.UUID
    aviso_id: uuid.UUID
    confirmado_at: datetime

    model_config = ConfigDict(from_attributes=True)

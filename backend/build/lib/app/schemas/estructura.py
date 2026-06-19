from __future__ import annotations

from pydantic import BaseModel
from pydantic import ConfigDict
from typing import Optional
import datetime


class CarreraCreate(BaseModel):
    codigo: str
    nombre: str

    model_config = ConfigDict(extra='forbid')


class CarreraUpdate(BaseModel):
    codigo: Optional[str] = None
    nombre: Optional[str] = None
    estado: Optional[str] = None

    model_config = ConfigDict(extra='forbid')


class CarreraResponse(BaseModel):
    id: str
    tenant_id: str
    codigo: str
    nombre: str
    estado: str
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class CohorteCreate(BaseModel):
    carrera_id: str
    nombre: str
    anio: int
    vig_desde: str
    vig_hasta: Optional[str] = None

    model_config = ConfigDict(extra='forbid')


class CohorteUpdate(BaseModel):
    nombre: Optional[str] = None
    anio: Optional[int] = None
    vig_desde: Optional[str] = None
    vig_hasta: Optional[str] = None
    estado: Optional[str] = None

    model_config = ConfigDict(extra='forbid')


class CohorteResponse(BaseModel):
    id: str
    tenant_id: str
    carrera_id: str
    nombre: str
    anio: int
    vig_desde: str
    vig_hasta: Optional[str]
    estado: str
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class MateriaCreate(BaseModel):
    codigo: str
    nombre: str

    model_config = ConfigDict(extra='forbid')


class MateriaUpdate(BaseModel):
    codigo: Optional[str] = None
    nombre: Optional[str] = None
    estado: Optional[str] = None

    model_config = ConfigDict(extra='forbid')


class MateriaResponse(BaseModel):
    id: str
    tenant_id: str
    codigo: str
    nombre: str
    estado: str
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

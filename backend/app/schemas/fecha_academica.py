from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.fecha_academica import TipoFechaAcademica


class FechaAcademicaCreate(BaseModel):
    materia_id: str
    cohorte_id: str
    tipo: TipoFechaAcademica
    numero: int = Field(ge=1)
    periodo: str
    fecha: str
    titulo: str

    model_config = ConfigDict(extra="forbid")


class FechaAcademicaUpdate(BaseModel):
    periodo: Optional[str] = None
    fecha: Optional[str] = None
    titulo: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


class FechaAcademicaResponse(BaseModel):
    id: str
    tenant_id: str
    materia_id: str
    cohorte_id: str
    tipo: str
    numero: int
    periodo: str
    fecha: str
    titulo: str
    created_at: str
    updated_at: str

    model_config = ConfigDict(from_attributes=True, extra="forbid")


class CalendarioPeriodo(BaseModel):
    periodo: str
    fechas: list[FechaAcademicaResponse]

    model_config = ConfigDict(extra="forbid")

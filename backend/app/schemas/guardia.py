"""Schemas Pydantic para el módulo de Guardias.

Todos con extra='forbid'.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.guardia import EstadoGuardia
from app.models.slot_encuentro import DiaSemana


class GuardiaCreate(BaseModel):
    """Schema para registrar una guardia."""

    model_config = ConfigDict(extra="forbid")

    asignacion_id: UUID = Field(..., description="UUID de la asignación del tutor")
    materia_id: UUID = Field(..., description="UUID de la materia")
    carrera_id: UUID = Field(..., description="UUID de la carrera")
    cohorte_id: UUID = Field(..., description="UUID de la cohorte")
    dia: DiaSemana = Field(..., description="Día de la semana")
    horario: str = Field(..., min_length=1, description="Rango horario (ej. 14:00–15:00)")
    comentarios: Optional[str] = Field(default=None, description="Comentarios opcionales")


class GuardiaCambiarEstado(BaseModel):
    """Schema para cambiar el estado de una guardia."""

    model_config = ConfigDict(extra="forbid")

    estado: EstadoGuardia = Field(..., description="Nuevo estado")


class GuardiaFiltros(BaseModel):
    """Query params para filtrar guardias."""

    model_config = ConfigDict(extra="forbid")

    materia_id: Optional[UUID] = Field(default=None)
    carrera_id: Optional[UUID] = Field(default=None)
    cohorte_id: Optional[UUID] = Field(default=None)
    estado: Optional[EstadoGuardia] = Field(default=None)
    asignacion_id: Optional[UUID] = Field(default=None)


class GuardiaResponse(BaseModel):
    """Respuesta completa de una guardia."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    tenant_id: UUID
    asignacion_id: UUID
    materia_id: UUID
    carrera_id: UUID
    cohorte_id: UUID
    dia: DiaSemana
    horario: str
    estado: EstadoGuardia
    comentarios: str | None = None
    creada_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

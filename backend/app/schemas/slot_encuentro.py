"""Schemas Pydantic para el módulo de Encuentros — Slot e Instancia.

Tres shapes de entrada/salida:
- SlotCreate: crear slot (recurrente o único).
- SlotResponse: detalle del slot con lista de instancias.
- InstanciaEdit: editar campos editables de una instancia.
- InstanciaResponse: respuesta completa de una instancia.

Todos con extra='forbid'.
"""

from __future__ import annotations

from datetime import date, time
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.instancia_encuentro import EstadoInstancia
from app.models.slot_encuentro import DiaSemana


class InstanciaResponse(BaseModel):
    """Respuesta completa de una instancia de encuentro."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    tenant_id: UUID
    slot_id: UUID | None = None
    materia_id: UUID
    fecha: date
    hora: time
    titulo: str
    estado: EstadoInstancia
    meet_url: str | None = None
    video_url: str | None = None
    comentario: str | None = None
    slot_titulo: str | None = Field(
        default=None,
        description="Título del slot padre (para vista admin)",
    )
    created_at: str | None = None
    updated_at: str | None = None


class SlotCreate(BaseModel):
    """Schema para crear un slot (recurrente o único)."""

    model_config = ConfigDict(extra="forbid")

    modo: str = Field(
        ...,
        description="'recurrente' (N semanas) o 'unico' (fecha concreta)",
        pattern=r"^(recurrente|unico)$",
    )
    asignacion_id: UUID = Field(..., description="UUID de la asignación del docente")
    materia_id: UUID = Field(..., description="UUID de la materia")
    titulo: str = Field(..., min_length=1, description="Título del encuentro")
    hora: time = Field(..., description="Hora del encuentro (HH:MM)")
    dia_semana: DiaSemana = Field(..., description="Día de la semana")
    fecha_inicio: date = Field(
        ...,
        description="Fecha del primer encuentro (debe coincidir con dia_semana si recurrente)",
    )
    cant_semanas: Optional[int] = Field(
        default=None,
        ge=1,
        description="N° de semanas (requerido si modo=recurrente, ≥1)",
    )
    fecha_unica: Optional[date] = Field(
        default=None,
        description="Fecha concreta (requerida si modo=unico)",
    )
    meet_url: Optional[str] = Field(default=None, description="URL de videoconferencia")
    vig_desde: date = Field(..., description="Inicio de vigencia")
    vig_hasta: Optional[date] = Field(default=None, description="Fin de vigencia (opcional)")

    @model_validator(mode="after")
    def _validate_modo(self) -> "SlotCreate":
        if self.modo == "recurrente":
            if self.cant_semanas is None:
                raise ValueError("cant_semanas es requerido para modo recurrente")
            if self.cant_semanas < 1:
                raise ValueError("cant_semanas debe ser ≥ 1 para modo recurrente")
            if self.fecha_unica is not None:
                raise ValueError("fecha_unica debe ser null para modo recurrente")
        elif self.modo == "unico":
            if self.cant_semanas is not None and self.cant_semanas > 0:
                raise ValueError("cant_semanas debe ser 0 para modo unico")
            if self.fecha_unica is None:
                raise ValueError("fecha_unica es requerida para modo unico")
        return self


class SlotResponse(BaseModel):
    """Respuesta de un slot con sus instancias."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    tenant_id: UUID
    asignacion_id: UUID
    materia_id: UUID
    titulo: str
    hora: time
    dia_semana: DiaSemana
    fecha_inicio: date
    cant_semanas: int
    fecha_unica: date | None = None
    meet_url: str | None = None
    vig_desde: date
    vig_hasta: date | None = None
    instancias: list[InstanciaResponse] = Field(
        default_factory=list,
        description="Instancias generadas a partir del slot",
    )
    created_at: str | None = None
    updated_at: str | None = None


class InstanciaEdit(BaseModel):
    """Schema para editar una instancia (PATCH).

    Al menos un campo debe ser provisto.
    """

    model_config = ConfigDict(extra="forbid")

    estado: Optional[EstadoInstancia] = Field(
        default=None,
        description="Nuevo estado (Programado | Realizado | Cancelado)",
    )
    meet_url: Optional[str] = Field(default=None, description="URL de videoconferencia")
    video_url: Optional[str] = Field(default=None, description="URL de grabación")
    comentario: Optional[str] = Field(default=None, description="Comentario del docente")

    @model_validator(mode="after")
    def _validate_at_least_one(self) -> "InstanciaEdit":
        if all(
            v is None
            for v in [self.estado, self.meet_url, self.video_url, self.comentario]
        ):
            raise ValueError("Al menos un campo editable debe ser provisto")
        return self

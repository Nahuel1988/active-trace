"""Pydantic v2 schemas para el módulo de calificaciones (C-10).

Todos los schemas de request usan ``extra='forbid'`` (regla dura R5).
"""

from __future__ import annotations

import datetime
import enum
import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class OrigenCalificacion(str, enum.Enum):
    """Origen de una calificación."""

    IMPORTADO = "importado"
    MANUAL = "manual"


# ---------------------------------------------------------------------------
# Request schemas — Calificacion
# ---------------------------------------------------------------------------


class CalificacionCreate(BaseModel):
    """Creación de una calificación.

    Se debe proporcionar al menos ``nota_numerica`` o ``nota_textual``.
    ``origen`` por defecto es ``importado``.
    """

    entrada_padron_id: uuid.UUID
    materia_id: uuid.UUID
    actividad: str = Field(..., min_length=1, max_length=255)
    nota_numerica: float | None = None
    nota_textual: str | None = None
    origen: OrigenCalificacion = OrigenCalificacion.IMPORTADO

    model_config = ConfigDict(extra="forbid")

    @field_validator("nota_numerica")
    @classmethod
    def validar_nota_numerica(cls, v: float | None) -> float | None:
        if v is not None and v < 0:
            raise ValueError("nota_numerica no puede ser negativa")
        return v

    @model_validator(mode="after")
    def al_menos_una_nota(self) -> "CalificacionCreate":
        if self.nota_numerica is None and self.nota_textual is None:
            raise ValueError("Debe proporcionar al menos una nota (nota_numerica o nota_textual)")
        return self


# ---------------------------------------------------------------------------
# Preview
# ---------------------------------------------------------------------------


class ColumnaDetectada(BaseModel):
    """Clasificación de una columna en el preview."""

    nombre: str
    tipo: str  # "numerica" | "textual" | "ignorada"

    model_config = ConfigDict(extra="forbid")


class PreviewResponse(BaseModel):
    """Respuesta del preview de archivo de calificaciones."""

    columnas_detectadas: list[dict[str, Any]]
    total_filas: int
    muestra_primeras_3: list[dict[str, str]]
    errores: list[str] = []

    model_config = ConfigDict(from_attributes=True, extra="forbid")


# ---------------------------------------------------------------------------
# Confirmar importación
# ---------------------------------------------------------------------------


class ConfirmarImportRequest(BaseModel):
    """Confirmación de importación de calificaciones."""

    materia_id: uuid.UUID
    actividades_seleccionadas: list[str]

    model_config = ConfigDict(extra="forbid")


# ---------------------------------------------------------------------------
# Response
# ---------------------------------------------------------------------------


class CalificacionResponse(BaseModel):
    """Respuesta de una calificación con ``aprobado`` derivado."""

    id: uuid.UUID
    entrada_padron_id: uuid.UUID
    materia_id: uuid.UUID
    actividad: str
    nota_numerica: float | None = None
    nota_textual: str | None = None
    aprobado: bool
    origen: str
    creado_por: uuid.UUID
    creada_at: str

    model_config = ConfigDict(from_attributes=True, extra="forbid")


# ---------------------------------------------------------------------------
# Umbral
# ---------------------------------------------------------------------------


class UmbralMateriaCreate(BaseModel):
    """Creación/actualización de umbral de materia."""

    umbral_pct: int = Field(..., ge=0, le=100)
    valores_aprobatorios: list[str] | None = None

    model_config = ConfigDict(extra="forbid")


class UmbralMateriaResponse(BaseModel):
    """Respuesta de un umbral de materia."""

    id: uuid.UUID
    asignacion_id: uuid.UUID
    materia_id: uuid.UUID
    umbral_pct: int
    valores_aprobatorios: list[str] | None = None

    model_config = ConfigDict(from_attributes=True, extra="forbid")


# ---------------------------------------------------------------------------
# Reporte de finalización
# ---------------------------------------------------------------------------


class ReporteFinalizacionItem(BaseModel):
    """Item del reporte de finalización: alumno × actividad sin calificar."""

    entrada_padron_id: uuid.UUID
    alumno: str
    actividad: str
    fecha_finalizacion: str

    model_config = ConfigDict(extra="forbid")


class ReporteFinalizacionResponse(BaseModel):
    """Respuesta del reporte de finalización."""

    items: list[ReporteFinalizacionItem]

    model_config = ConfigDict(from_attributes=True, extra="forbid")


# ---------------------------------------------------------------------------
# Vaciar
# ---------------------------------------------------------------------------


class VaciarRequest(BaseModel):
    """Solicitud de vaciado de calificaciones de una materia."""

    materia_id: uuid.UUID

    model_config = ConfigDict(extra="forbid")

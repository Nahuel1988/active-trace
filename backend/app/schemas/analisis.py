"""Schemas for análisis and monitor modules (C-11).

All request schemas use ``extra='forbid'`` (regla dura R5).
"""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict


class AtrasadoItem(BaseModel):
    """Un alumno clasificado como atrasado."""

    entrada_padron_id: uuid.UUID
    alumno_nombre: str
    alumno_apellido: str
    email: str | None = None
    materia_id: uuid.UUID
    materia_nombre: str
    clasificacion: str  # "missing" | "below_threshold"
    actividad: str | None = None

    model_config = ConfigDict(from_attributes=True, extra="forbid")


class AtrasadosResponse(BaseModel):
    """Respuesta del endpoint de atrasados."""

    items: list[AtrasadoItem]
    total: int

    model_config = ConfigDict(extra="forbid")


class RankingItem(BaseModel):
    """Item del ranking de actividades aprobadas."""

    entrada_padron_id: uuid.UUID
    alumno_nombre: str
    alumno_apellido: str
    actividades_aprobadas: int
    total_actividades: int
    porcentaje_aprobacion: float

    model_config = ConfigDict(from_attributes=True, extra="forbid")


class RankingResponse(BaseModel):
    """Respuesta del endpoint de ranking."""

    items: list[RankingItem]

    model_config = ConfigDict(extra="forbid")


class ReporteRapidoResponse(BaseModel):
    """Respuesta del endpoint de reporte rápido."""

    total_alumnos: int
    total_actividades: int
    tasa_aprobacion_pct: float
    alumnos_atrasados: int
    alumnos_al_dia: int
    sin_datos: bool = False

    model_config = ConfigDict(extra="forbid")


class NotaActividad(BaseModel):
    """Desglose de nota por actividad."""

    actividad: str
    nota_numerica: float | None = None
    nota_textual: str | None = None
    aprobado: bool

    model_config = ConfigDict(extra="forbid")


class NotaFinalAlumno(BaseModel):
    """Notas finales de un alumno."""

    entrada_padron_id: uuid.UUID
    alumno_nombre: str
    alumno_apellido: str
    actividades: list[NotaActividad]
    promedio_numerico: float | None = None
    actividades_textuales: list[NotaActividad] = []

    model_config = ConfigDict(extra="forbid")


class NotasFinalesResponse(BaseModel):
    """Respuesta del endpoint de notas finales."""

    items: list[NotaFinalAlumno]

    model_config = ConfigDict(extra="forbid")


class EntregaPendienteItem(BaseModel):
    """Item de entrega pendiente de corrección."""

    alumno: str
    actividad: str
    fecha_submission: str
    materia: str

    model_config = ConfigDict(extra="forbid")


class EntregasPendientesResponse(BaseModel):
    """Respuesta del endpoint de entregas pendientes."""

    items: list[EntregaPendienteItem]
    todas_corregidas: bool = False

    model_config = ConfigDict(extra="forbid")


class MonitorItem(BaseModel):
    """Item del monitor de alumnos."""

    entrada_padron_id: uuid.UUID
    alumno_nombre: str
    alumno_apellido: str
    email: str | None = None
    materia_id: uuid.UUID | None = None
    materia_nombre: str
    comision: str
    actividades_aprobadas: int
    actividades_pendientes: int
    atrasado: bool

    model_config = ConfigDict(from_attributes=True, extra="forbid")


class MonitorResponse(BaseModel):
    """Respuesta paginada del monitor."""

    items: list[MonitorItem]
    total: int
    limit: int
    offset: int

    model_config = ConfigDict(extra="forbid")

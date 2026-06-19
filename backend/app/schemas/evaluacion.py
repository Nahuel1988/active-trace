from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ── Evaluacion ──────────────────────────────────────────────────────────────


class EvaluacionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    materia_id: UUID = Field(..., description="UUID de la materia")
    cohorte_id: UUID = Field(..., description="UUID de la cohorte")
    tipo: str = Field(default="Coloquio", description="Parcial | TP | Coloquio | Recuperatorio")
    instancia: str = Field(..., description="Denominación de la instancia")
    dias_disponibles: int = Field(..., ge=1, description="Ventana en días (cupo total)")


class EvaluacionUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    materia_id: Optional[UUID] = None
    cohorte_id: Optional[UUID] = None
    tipo: Optional[str] = None
    instancia: Optional[str] = None
    dias_disponibles: Optional[int] = Field(default=None, ge=1)


class EvaluacionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    tenant_id: UUID
    materia_id: UUID
    cohorte_id: UUID
    tipo: str
    instancia: str
    dias_disponibles: int
    created_at: datetime
    updated_at: datetime


class EvaluacionConMetricas(EvaluacionResponse):
    """EvaluacionResponse extendido con métricas operativas."""

    convocados: int = 0
    reservas_activas: int = 0
    cupos_libres: int = 0


# ── Candidatos ──────────────────────────────────────────────────────────────


class CandidatosImportRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    usuario_ids: List[UUID] = Field(..., description="Lista de UUIDs de alumnos a importar")


class CandidatoRechazado(BaseModel):
    model_config = ConfigDict(extra="forbid")

    usuario_id: UUID
    motivo: str


class CandidatosImportResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    registrados: int
    rechazados: List[CandidatoRechazado]


# ── Metrics ─────────────────────────────────────────────────────────────────


class MetricasPanel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_candidatos: int = 0
    instancias_activas: int = 0
    reservas_activas: int = 0
    notas_registradas: int = 0


# ── Agenda ──────────────────────────────────────────────────────────────────


class AgendaItem(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    reserva_id: UUID
    evaluacion_id: UUID
    materia_id: UUID
    materia_nombre: Optional[str] = None
    cohorte_id: UUID
    instancia: str
    tipo: str
    alumno_id: UUID
    alumno_nombre: Optional[str] = None
    alumno_legajo: Optional[str] = None
    fecha_hora: datetime
    estado: str


# ── ReservaEvaluacion ───────────────────────────────────────────────────────


class ReservaCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fecha_hora: datetime = Field(..., description="Fecha y hora del turno")


class ReservaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    tenant_id: UUID
    evaluacion_id: UUID
    alumno_id: UUID
    fecha_hora: datetime
    estado: str
    created_at: datetime
    updated_at: datetime


class MisReservasItem(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    evaluacion_id: UUID
    alumno_id: UUID
    materia_nombre: Optional[str] = None
    instancia: str
    fecha_hora: datetime
    estado: str


# ── ResultadoEvaluacion ─────────────────────────────────────────────────────


class ResultadoCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    alumno_id: UUID = Field(..., description="UUID del alumno")
    nota_final: str = Field(..., description="Nota (numérica o cualitativa)")


class ResultadoUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nota_final: str = Field(..., description="Nueva nota")


class ResultadoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    tenant_id: UUID
    evaluacion_id: UUID
    alumno_id: UUID
    nota_final: str
    created_at: datetime
    updated_at: datetime


class ResultadoConAlumno(ResultadoResponse):
    """ResultadoResponse con datos del alumno."""

    alumno_nombre: Optional[str] = None
    alumno_legajo: Optional[str] = None


class RegistroAcademicoItem(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    resultado_id: UUID
    evaluacion_id: UUID
    materia_id: UUID
    materia_nombre: Optional[str] = None
    cohorte_id: UUID
    instancia: str
    tipo: str
    alumno_id: UUID
    alumno_nombre: Optional[str] = None
    alumno_legajo: Optional[str] = None
    nota_final: str
    created_at: datetime

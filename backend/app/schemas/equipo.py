"""Schemas Pydantic para el módulo de Equipos — C-08.

Operaciones de bloque sobre Asignacion agrupadas por tupla
(materia_id, carrera_id, cohorte_id).

Todos con extra='forbid'.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class EquipoResumen(BaseModel):
    """Tupla (materia, carrera, cohorte) con conteo de asignaciones vigentes."""

    model_config = ConfigDict(extra="forbid")

    materia_id: Optional[str] = None
    carrera_id: Optional[str] = None
    cohorte_id: Optional[str] = None
    conteo: int = Field(..., ge=0)
    materia_nombre: Optional[str] = None
    carrera_nombre: Optional[str] = None
    cohorte_nombre: Optional[str] = None


class AsignacionEquipoItem(BaseModel):
    """Ítem de asignación dentro de un equipo (sin PII)."""

    model_config = ConfigDict(extra="forbid")

    id: str
    role_id: str
    comisiones: List[str] = Field(default_factory=list)
    responsable_id: Optional[str] = None
    desde: datetime
    hasta: Optional[datetime] = None
    estado_vigencia: str
    usuario_id: str
    usuario_nombre: Optional[str] = None
    usuario_apellidos: Optional[str] = None
    usuario_legajo: Optional[str] = None


class MisEquiposResponse(BaseModel):
    """Asignaciones del usuario agrupadas por tupla de equipo."""

    model_config = ConfigDict(extra="forbid")

    materia_id: Optional[str] = None
    carrera_id: Optional[str] = None
    cohorte_id: Optional[str] = None
    asignaciones: List[AsignacionEquipoItem] = Field(default_factory=list)


class AsignacionMasivaRequest(BaseModel):
    """Request de asignación masiva.

    Crea asignaciones para múltiples usuarios en el mismo contexto.
    """

    model_config = ConfigDict(extra="forbid")

    usuario_ids: List[str] = Field(..., min_length=1, description="UUIDs de usuarios a asignar")
    role_id: str = Field(..., description="UUID del rol")
    materia_id: Optional[str] = None
    carrera_id: Optional[str] = None
    cohorte_id: Optional[str] = None
    comisiones: List[str] = Field(default_factory=list)
    responsable_id: Optional[str] = None
    desde: datetime = Field(..., description="Inicio de vigencia")
    hasta: Optional[datetime] = None


class AsignacionMasivaItem(BaseModel):
    """Ítem de resumen (rechazada u omitida)."""

    model_config = ConfigDict(extra="forbid")

    usuario_id: str
    motivo: str


class AsignacionMasivaResponse(BaseModel):
    """Respuesta de asignación masiva: resumen best-effort."""

    model_config = ConfigDict(extra="forbid")

    creadas: int = 0
    rechazadas: List[AsignacionMasivaItem] = Field(default_factory=list)
    omitidas: List[AsignacionMasivaItem] = Field(default_factory=list)


class ClonarEquipoRequest(BaseModel):
    """Request de clonado de equipo entre períodos (RN-12)."""

    model_config = ConfigDict(extra="forbid")

    origen_materia_id: str = Field(..., description="Materia origen")
    origen_carrera_id: str = Field(..., description="Carrera origen")
    origen_cohorte_id: str = Field(..., description="Cohorte origen")
    destino_carrera_id: str = Field(..., description="Carrera destino")
    destino_cohorte_id: str = Field(..., description="Cohorte destino")
    destino_materia_id: Optional[str] = Field(default=None, description="Materia destino (default = misma materia)")
    nuevo_desde: datetime = Field(..., description="Inicio de vigencia en destino")
    nuevo_hasta: Optional[datetime] = None


class ClonarEquipoResponse(BaseModel):
    """Respuesta de clonado de equipo."""

    model_config = ConfigDict(extra="forbid")

    clonadas: int = 0
    omitidas: List[AsignacionMasivaItem] = Field(default_factory=list)


class VigenciaBloqueRequest(BaseModel):
    """Request de actualización masiva de vigencia en bloque."""

    model_config = ConfigDict(extra="forbid")

    materia_id: Optional[str] = None
    carrera_id: Optional[str] = None
    cohorte_id: Optional[str] = None
    desde: datetime = Field(..., description="Nuevo inicio de vigencia")
    hasta: Optional[datetime] = None


class VigenciaBloqueResponse(BaseModel):
    """Respuesta de actualización de vigencia en bloque."""

    model_config = ConfigDict(extra="forbid")

    filas_afectadas: int = 0

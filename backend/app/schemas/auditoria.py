from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

#: Tope máximo de seguridad para limit en consultas de auditoría.
AUDIT_LOG_MAX_LIMIT = 1000


class AuditoriaFiltros(BaseModel):
    """Filtros opcionales para consultas de auditoría (query params).

    Todos los campos son opcionales. ``limit`` tiene un máximo de seguridad
    ``AUDIT_LOG_MAX_LIMIT``.
    """

    desde: datetime | None = None
    hasta: datetime | None = None
    materia_id: UUID | None = None
    actor_id: UUID | None = None
    accion: str | None = None
    limit: int = Field(default=200, ge=1, le=AUDIT_LOG_MAX_LIMIT)
    offset: int = Field(default=0, ge=0)

    model_config = ConfigDict(extra="forbid")


class AccionesPorDiaItem(BaseModel):
    """Una fila de la agregación de acciones por día."""

    fecha: datetime
    total: int

    model_config = ConfigDict(from_attributes=True)


class AccionesPorDiaResponse(BaseModel):
    """Respuesta del endpoint acciones-por-dia."""

    data: list[AccionesPorDiaItem]

    model_config = ConfigDict(extra="forbid")


class ComunicacionesPorDocenteItem(BaseModel):
    """Distribución de un código de comunicación para un actor."""

    actor_id: UUID
    accion: str
    total: int

    model_config = ConfigDict(from_attributes=True)


class ComunicacionesPorDocenteResponse(BaseModel):
    """Respuesta del endpoint comunicaciones-por-docente."""

    data: list[ComunicacionesPorDocenteItem]

    model_config = ConfigDict(extra="forbid")


class InteraccionesItem(BaseModel):
    """Conteo de interacciones por actor, materia y acción."""

    actor_id: UUID
    materia_id: UUID | str | None
    accion: str
    total: int

    model_config = ConfigDict(from_attributes=True)


class InteraccionesResponse(BaseModel):
    """Respuesta del endpoint interacciones."""

    data: list[InteraccionesItem]

    model_config = ConfigDict(extra="forbid")


class UltimasAccionesItem(BaseModel):
    """Una entrada individual del log de últimas acciones (RN-23)."""

    id: UUID
    fecha_hora: datetime
    actor_id: UUID
    materia_id: UUID | None
    accion: str
    filas_afectadas: int
    ip: str
    user_agent: str

    model_config = ConfigDict(from_attributes=True)


class UltimasAccionesResponse(BaseModel):
    """Respuesta del endpoint últimas-acciones."""

    data: list[UltimasAccionesItem]
    total: int | None = None

    model_config = ConfigDict(extra="forbid")


class LogItem(BaseModel):
    """Una entrada del log completo de auditoría (F9.2, RN-23)."""

    id: UUID
    fecha_hora: datetime
    actor_id: UUID
    materia_id: UUID | None
    accion: str
    detalle: dict
    filas_afectadas: int
    ip: str
    user_agent: str

    model_config = ConfigDict(from_attributes=True)


class LogResponse(BaseModel):
    """Respuesta paginada del log completo de auditoría."""

    data: list[LogItem]
    total: int | None = None

    model_config = ConfigDict(extra="forbid")

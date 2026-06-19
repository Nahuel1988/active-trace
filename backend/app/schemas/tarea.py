"""Pydantic v2 schemas para el módulo de tareas internas (C-16).

Todos los schemas de request usan ``extra='forbid'`` (regla dura R5).
"""

from __future__ import annotations

import datetime
import uuid
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.tarea import EstadoTarea


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class TareaCreate(BaseModel):
    """Creación de una tarea.

    ``asignado_por`` NO se acepta del body (viene de la sesión JWT).
    ``materia_id`` y ``contexto_id`` son opcionales.
    """

    asignado_a: uuid.UUID
    descripcion: str
    materia_id: Optional[uuid.UUID] = None
    contexto_id: Optional[uuid.UUID] = None

    model_config = ConfigDict(extra="forbid")


class TareaDelegar(BaseModel):
    """Delegar/re-asignar una tarea a otro usuario."""

    asignado_a: uuid.UUID

    model_config = ConfigDict(extra="forbid")


class TareaCambiarEstado(BaseModel):
    """Cambiar el estado de una tarea."""

    estado: EstadoTarea

    model_config = ConfigDict(extra="forbid")


class ComentarioCreate(BaseModel):
    """Crear un comentario en una tarea.

    ``autor_id`` NO se acepta del body (viene de la sesión JWT).
    """

    texto: str

    model_config = ConfigDict(extra="forbid")


# ---------------------------------------------------------------------------
# Filtros (query params)
# ---------------------------------------------------------------------------


class TareaFiltros(BaseModel):
    """Filtros opcionales para el listado de tareas.

    Todos son opcionales. ``q`` hace ILIKE sobre ``descripcion``.
    """

    asignado_a: Optional[uuid.UUID] = None
    asignado_por: Optional[uuid.UUID] = None
    materia_id: Optional[uuid.UUID] = None
    estado: Optional[EstadoTarea] = None
    q: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class TareaResponse(BaseModel):
    """Respuesta completa de una tarea."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    asignado_a: uuid.UUID
    asignado_por: uuid.UUID
    materia_id: Optional[uuid.UUID] = None
    contexto_id: Optional[uuid.UUID] = None
    descripcion: str
    estado: EstadoTarea
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class ComentarioResponse(BaseModel):
    """Respuesta de un comentario en una tarea."""

    id: uuid.UUID
    tarea_id: uuid.UUID
    autor_id: uuid.UUID
    texto: str
    creado_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

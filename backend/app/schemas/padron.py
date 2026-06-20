"""Pydantic v2 schemas para el módulo de padrón (C-09).

Todos los schemas de request usan ``extra='forbid'`` (regla dura R5).
"""

from __future__ import annotations

import datetime
import uuid
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class EntradaPadronCreate(BaseModel):
    """Una entrada de padrón recibida del cliente (archivo o body).

    ``usuario_id`` es nullable: alumno puede no tener cuenta.
    El ``email`` se validará con formato estándar.
    """

    nombre: str = Field(..., min_length=1, max_length=255)
    apellidos: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    comision: str = Field(..., min_length=1, max_length=100)
    regional: Optional[str] = Field(None, max_length=255)
    usuario_id: Optional[uuid.UUID] = None

    model_config = ConfigDict(extra="forbid", json_schema_extra={
        "example": {
            "nombre": "Juan",
            "apellidos": "Pérez",
            "email": "juan@example.com",
            "comision": "A",
            "regional": "CABA",
            "usuario_id": None,
        },
    })


class EntradaPadronPreview(BaseModel):
    """Versión de preview de una entrada (sin validar email formato aún)."""

    nombre: str
    apellidos: str
    email: str
    comision: str
    regional: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


class ConfirmarRequest(BaseModel):
    """Confirmación de carga de padrón.

    Recibe la lista completa de entradas (los datos ya parseados del preview).
    """

    materia_id: uuid.UUID
    cohorte_id: uuid.UUID
    entradas: list[EntradaPadronCreate]

    model_config = ConfigDict(extra="forbid")


class VaciarRequest(BaseModel):
    """Solicitud de vaciado de padrón de una materia."""

    materia_id: uuid.UUID

    model_config = ConfigDict(extra="forbid")


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class PreviewResponse(BaseModel):
    """Respuesta del preview de archivo de padrón."""

    total_filas: int
    columnas_detectadas: list[str]
    muestra: list[EntradaPadronPreview]
    errores: list[str] = []

    model_config = ConfigDict(from_attributes=True)


class VersionPadronResponse(BaseModel):
    """Respuesta de una versión de padrón."""

    id: uuid.UUID
    materia_id: uuid.UUID
    cohorte_id: uuid.UUID
    activa: bool
    total_entradas: int
    origen: str
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class ConfirmarResponse(BaseModel):
    """Respuesta tras confirmar una carga de padrón."""

    version_id: uuid.UUID
    total_entradas: int
    origen: str
    mensaje: str = "Padrón cargado exitosamente"

    model_config = ConfigDict(from_attributes=True)


class MoodleSyncResponse(BaseModel):
    """Respuesta tras sincronizar padrón desde Moodle."""

    version_id: uuid.UUID
    total_sincronizadas: int
    errores: list[str] = []

    model_config = ConfigDict(from_attributes=True)


class EntradaPadronResponse(BaseModel):
    """Respuesta de una entrada individual (email desencriptado)."""

    id: uuid.UUID
    version_padron_id: uuid.UUID
    nombre: str
    apellidos: str
    email: str
    comision: str
    regional: Optional[str] = None
    usuario_id: Optional[uuid.UUID] = None

    model_config = ConfigDict(from_attributes=True)


class VersionPadronListResponse(BaseModel):
    """Lista de versiones de padrón."""

    versiones: list[VersionPadronResponse]
    total: int

    model_config = ConfigDict(from_attributes=True)

"""Schemas Pydantic para el módulo de Asignaciones — C-07.

Tres shapes:
- AsignacionCreate: crear vinculación usuario × rol × contexto académico.
- AsignacionUpdate: actualizar campos opcionales de una asignación.
- AsignacionResponse: respuesta con sub-objeto UsuarioMinimo (sin PII sensible).

Todos con extra='forbid'.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.usuario import UsuarioMinimo


class AsignacionCreate(BaseModel):
    """Schema para crear una asignación.

    El tenant_id se extrae del JWT del caller — NO se acepta en el body.
    La combinación rol × contexto se valida en AsignacionService.
    """

    model_config = ConfigDict(extra="forbid")

    usuario_id: str = Field(..., description="UUID del usuario a asignar")
    role_id: str = Field(..., description="UUID del rol asignado")
    materia_id: Optional[str] = Field(default=None, description="UUID de la materia (nullable)")
    carrera_id: Optional[str] = Field(default=None, description="UUID de la carrera (nullable)")
    cohorte_id: Optional[str] = Field(default=None, description="UUID de la cohorte (nullable)")
    comisiones: List[str] = Field(default_factory=list, description="Lista de comisiones (puede ser vacía)")
    responsable_id: Optional[str] = Field(default=None, description="UUID del responsable jerárquico (nullable)")
    desde: datetime = Field(..., description="Fecha de inicio de vigencia (NOT NULL)")
    hasta: Optional[datetime] = Field(default=None, description="Fecha de fin de vigencia (NULL = indefinida)")


class AsignacionUpdate(BaseModel):
    """Schema para actualizar una asignación.

    Solo se aceptan los campos modificables. usuario_id y role_id
    no son actualizables — crear una nueva asignación si cambian.
    """

    model_config = ConfigDict(extra="forbid")

    materia_id: Optional[str] = Field(default=None)
    carrera_id: Optional[str] = Field(default=None)
    cohorte_id: Optional[str] = Field(default=None)
    comisiones: Optional[List[str]] = Field(default=None)
    responsable_id: Optional[str] = Field(default=None)
    desde: Optional[datetime] = Field(default=None)
    hasta: Optional[datetime] = Field(default=None)


class AsignacionResponse(BaseModel):
    """Schema de respuesta para asignaciones.

    Incluye sub-objeto UsuarioMinimo con {id, nombre, apellidos, legajo}
    sin exponer PII sensible (dni, cuil, cbu, alias_cbu, email).
    """

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: str
    tenant_id: str
    usuario_id: str
    role_id: str
    materia_id: Optional[str] = None
    carrera_id: Optional[str] = None
    cohorte_id: Optional[str] = None
    comisiones: List[str] = Field(default_factory=list)
    responsable_id: Optional[str] = None
    desde: datetime
    hasta: Optional[datetime] = None
    estado_vigencia: str = Field(description="'Vigente' o 'Vencida' (derivado de fechas)")
    usuario: UsuarioMinimo = Field(description="Sub-objeto usuario sin PII sensible")
    created_at: datetime
    updated_at: datetime

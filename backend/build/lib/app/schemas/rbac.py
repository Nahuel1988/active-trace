"""Pydantic v2 schemas for RBAC administration endpoints.

Todos los schemas usan ``extra='forbid'`` según convención del proyecto.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ── Request Schemas ────────────────────────────────────────────────────────


class PermisoCreate(BaseModel):
    """Request body for creating a new permission.

    Attributes:
        modulo: Módulo funcional (ej: ``comunicacion``).
        accion: Acción dentro del módulo (ej: ``aprobar``).
    """
    model_config = ConfigDict(extra='forbid')

    modulo: str = Field(
        ...,
        min_length=1,
        max_length=100,
        pattern=r'^[a-z_]+$',
        description="Módulo funcional (solo minúsculas y guión bajo)",
    )
    accion: str = Field(
        ...,
        min_length=1,
        max_length=100,
        pattern=r'^[a-z_]+$',
        description="Acción dentro del módulo (solo minúsculas y guión bajo)",
    )

    @field_validator('modulo', 'accion')
    @classmethod
    def _no_spaces(cls, v: str) -> str:
        if ' ' in v:
            raise ValueError('No se permiten espacios')
        return v.strip()


class PermisoUpdate(BaseModel):
    """Request body for updating a permission."""
    model_config = ConfigDict(extra='forbid')

    modulo: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        pattern=r'^[a-z_]+$',
    )
    accion: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        pattern=r'^[a-z_]+$',
    )


class RolPermisoAsignar(BaseModel):
    """Request body for assigning a permission to a role.

    Attributes:
        role_code: Código del rol (ej: ``profesor``).
        permiso_code: Código del permiso (ej: ``comunicacion:enviar``).
        scope: Alcance — ``"global"`` o ``"propio"``.
    """
    model_config = ConfigDict(extra='forbid')

    role_code: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Código del rol (ej: profesor)",
    )
    permiso_code: str = Field(
        ...,
        min_length=1,
        max_length=201,
        pattern=r'^[a-z_]+:[a-z_]+$',
        description="Código del permiso (ej: comunicacion:enviar)",
    )
    scope: str = Field(
        ...,
        pattern=r'^(global|propio)$',
        description="Alcance: 'global' o 'propio'",
    )


# ── Response Schemas ───────────────────────────────────────────────────────


class PermisoResponse(BaseModel):
    """Response body for a single permission."""
    model_config = ConfigDict(extra='forbid')

    id: str
    modulo: str
    accion: str
    code: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


class RolPermisoResponse(BaseModel):
    """Response body for a single role-permission assignment row."""
    model_config = ConfigDict(extra='forbid')

    role_code: str
    permiso_code: str
    scope: str
    created_at: datetime | None = None


class MatrizRow(BaseModel):
    """A single row in the permission matrix response."""
    model_config = ConfigDict(extra='forbid')

    role_code: str
    role_nombre: str
    permiso_code: str
    permiso_modulo: str
    permiso_accion: str
    scope: str


class RoleResponse(BaseModel):
    """Response body for a single role."""
    model_config = ConfigDict(extra='forbid')

    id: str
    code: str
    nombre: str
    created_at: datetime | None = None

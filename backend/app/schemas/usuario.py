"""Schemas Pydantic para el módulo de Usuarios — C-07.

Tres shapes:
- UsuarioCreate: admin crea usuario con PII en claro (cifrado ocurre en repository).
- UsuarioUpdate: todos los campos opcionales; solo se cifra lo que venga.
- UsuarioResponse: devuelve PII descifrada (solo para caller con usuarios:gestionar).

Todos con extra='forbid'.
PII sensible (dni, cuil, cbu, alias_cbu, email, password) se oculta en __repr__.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# Campos PII que NO deben aparecer en repr/logs
_PII_FIELDS = frozenset({"dni", "cuil", "cbu", "alias_cbu", "email", "password"})


def _mask_pii(data: dict) -> dict:
    """Retorna una copia del dict con PII enmascarada."""
    return {k: ("***" if k in _PII_FIELDS and v is not None else v) for k, v in data.items()}


class UsuarioCreate(BaseModel):
    """Schema para crear un usuario vía el endpoint admin.

    Los campos PII (dni, cuil, cbu, alias_cbu) se reciben en claro
    y son cifrados en el repository antes de persistir.
    """

    model_config = ConfigDict(extra="forbid")

    email: str = Field(..., description="Email institucional del usuario")
    password: str = Field(..., description="Password en claro (hash en el service)")
    nombre: str = Field(..., description="Nombre/s del usuario")
    apellidos: str = Field(..., description="Apellido/s del usuario")
    legajo: Optional[str] = Field(default=None, description="Legajo del alumno (NO credencial)")
    legajo_profesional: Optional[str] = Field(default=None, description="Legajo profesional")
    banco: Optional[str] = Field(default=None, description="Banco del usuario")
    regional: Optional[str] = Field(default=None, description="Regional/sede")

    # PII cifrada en reposo — se reciben en claro para ser cifrados en el repository
    dni: Optional[str] = Field(default=None, repr=False, description="DNI (se cifra)")
    cuil: Optional[str] = Field(default=None, repr=False, description="CUIL (se cifra)")
    cbu: Optional[str] = Field(default=None, repr=False, description="CBU (se cifra)")
    alias_cbu: Optional[str] = Field(default=None, repr=False, description="Alias CBU (se cifra)")

    facturador: bool = Field(default=False, description="¿El usuario emite facturas?")

    def __repr__(self) -> str:
        data = self.model_dump()
        masked = _mask_pii(data)
        fields_str = ", ".join(f"{k}={v!r}" for k, v in masked.items())
        return f"UsuarioCreate({fields_str})"

    def __str__(self) -> str:
        return self.__repr__()


class UsuarioUpdate(BaseModel):
    """Schema para actualizar un usuario vía el endpoint admin.

    Todos los campos son opcionales; solo se cifra la PII que venga.
    """

    model_config = ConfigDict(extra="forbid")

    nombre: Optional[str] = Field(default=None)
    apellidos: Optional[str] = Field(default=None)
    legajo: Optional[str] = Field(default=None)
    legajo_profesional: Optional[str] = Field(default=None)
    banco: Optional[str] = Field(default=None)
    regional: Optional[str] = Field(default=None)
    is_active: Optional[bool] = Field(default=None)
    facturador: Optional[bool] = Field(default=None)

    # PII — repr=False para enmascarar en logs
    dni: Optional[str] = Field(default=None, repr=False)
    cuil: Optional[str] = Field(default=None, repr=False)
    cbu: Optional[str] = Field(default=None, repr=False)
    alias_cbu: Optional[str] = Field(default=None, repr=False)

    def __repr__(self) -> str:
        data = self.model_dump(exclude_none=True)
        masked = _mask_pii(data)
        fields_str = ", ".join(f"{k}={v!r}" for k, v in masked.items())
        return f"UsuarioUpdate({fields_str})"

    def __str__(self) -> str:
        return self.__repr__()


class UsuarioResponse(BaseModel):
    """Schema de respuesta para el endpoint admin.

    Devuelve PII descifrada — SOLO usar para callers con usuarios:gestionar.
    Para otros endpoints usar UsuarioMinimo.
    """

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: str
    tenant_id: str
    email: Optional[str] = Field(default=None, repr=False, description="Email descifrado")
    nombre: Optional[str] = None
    apellidos: Optional[str] = None
    legajo: Optional[str] = None
    legajo_profesional: Optional[str] = None
    banco: Optional[str] = None
    regional: Optional[str] = None
    facturador: bool = False
    is_active: bool = True

    # PII descifrada — solo visible para ADMIN
    dni: Optional[str] = Field(default=None, repr=False)
    cuil: Optional[str] = Field(default=None, repr=False)
    cbu: Optional[str] = Field(default=None, repr=False)
    alias_cbu: Optional[str] = Field(default=None, repr=False)

    created_at: datetime
    updated_at: datetime


class UsuarioMinimo(BaseModel):
    """Sub-objeto de usuario sin PII sensible.

    Usado en AsignacionResponse y cualquier endpoint que NO tenga
    el permiso usuarios:gestionar.
    """

    model_config = ConfigDict(from_attributes=True)

    id: str
    nombre: Optional[str] = None
    apellidos: Optional[str] = None
    legajo: Optional[str] = None

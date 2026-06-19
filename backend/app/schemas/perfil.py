"""Schemas Pydantic para el módulo de Perfil propio — C-20.

Dos shapes:
- PerfilRead: respuesta al dueño del perfil con PII descifrada.
  Expone cuil (read-only), dni, cbu, alias_cbu en claro (solo para el dueño).
- PerfilUpdate: payload de actualización.
  SIN campo cuil — extra='forbid' → 422 si el cliente intenta enviarlo.
  Valida modalidad_cobro (solo 'factura' | 'liquidacion').

Ambos con extra='forbid'.
PII sensible marcada con repr=False para no aparecer en logs.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

# Valores permitidos para modalidad_cobro
ModalidadCobro = Literal["factura", "liquidacion"]


class PerfilRead(BaseModel):
    """Respuesta al dueño del perfil con PII descifrada.

    SOLO usar en GET /api/perfil (propio dueño).
    No exponer en listados ni en el inbox.
    """

    model_config = ConfigDict(extra="forbid")

    id: str
    tenant_id: str

    # Identidad pública
    email: Optional[str] = Field(default=None, repr=False, description="Email descifrado")
    nombre: Optional[str] = None
    apellidos: Optional[str] = None
    legajo: Optional[str] = None
    legajo_profesional: Optional[str] = None
    banco: Optional[str] = None
    regional: Optional[str] = None
    facturador: bool = False
    is_active: bool = True
    modalidad_cobro: Optional[ModalidadCobro] = None

    # PII descifrada — solo para el dueño, nunca en otros endpoints
    dni: Optional[str] = Field(default=None, repr=False, description="DNI descifrado")
    cuil: Optional[str] = Field(
        default=None,
        repr=False,
        description="CUIL descifrado — solo lectura; no modificable vía /api/perfil",
    )
    cbu: Optional[str] = Field(default=None, repr=False, description="CBU descifrado")
    alias_cbu: Optional[str] = Field(default=None, repr=False, description="Alias CBU descifrado")


class PerfilUpdate(BaseModel):
    """Payload para PATCH /api/perfil.

    Excluye deliberadamente el campo `cuil`: con extra='forbid' cualquier
    intento de enviarlo retorna 422 (D2 del design.md).
    La identidad del usuario que se actualiza SIEMPRE viene del JWT, nunca del body.
    """

    model_config = ConfigDict(extra="forbid")

    nombre: Optional[str] = Field(default=None, description="Nombre/s del usuario")
    apellidos: Optional[str] = Field(default=None, description="Apellido/s del usuario")
    legajo_profesional: Optional[str] = Field(default=None, description="Legajo profesional")
    banco: Optional[str] = Field(default=None, description="Banco")
    regional: Optional[str] = Field(default=None, description="Regional/sede")
    modalidad_cobro: Optional[ModalidadCobro] = Field(
        default=None,
        description="Modalidad de cobro: 'factura' o 'liquidacion'",
    )

    # PII editables — repr=False para enmascarar en logs
    dni: Optional[str] = Field(default=None, repr=False, description="DNI (se cifra en reposo)")
    cbu: Optional[str] = Field(default=None, repr=False, description="CBU (se cifra en reposo)")
    alias_cbu: Optional[str] = Field(
        default=None, repr=False, description="Alias CBU (se cifra en reposo)"
    )
    # `cuil` está AUSENTE — extra='forbid' garantiza que enviarlo devuelve 422

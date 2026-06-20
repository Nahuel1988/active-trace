"""Schemas Pydantic para SalarioPlus (plus salarial por grupo y rol)."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, model_validator


class SalarioPlusCreate(BaseModel):
    """Schema para crear un plus salarial."""

    grupo: str
    rol: str
    descripcion: str
    monto: Decimal
    desde: date
    hasta: date | None = None

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def hasta_posterior_a_desde(self) -> "SalarioPlusCreate":
        if self.hasta is not None and self.hasta < self.desde:
            raise ValueError("'hasta' debe ser posterior o igual a 'desde'")
        return self


class SalarioPlusUpdate(BaseModel):
    """Schema para actualizar descripción, monto y/o vigencia de cierre."""

    descripcion: str | None = None
    monto: Decimal | None = None
    hasta: date | None = None

    model_config = ConfigDict(extra="forbid")


class SalarioPlusResponse(BaseModel):
    """Schema de respuesta con todos los campos de SalarioPlus."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    grupo: str
    rol: str
    descripcion: str
    monto: Decimal
    desde: date
    hasta: date | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, extra="forbid")

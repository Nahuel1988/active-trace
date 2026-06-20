"""Schemas Pydantic para SalarioBase (grilla salarial por rol)."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, model_validator

from app.models.salario_base import RolLiquidacion


class SalarioBaseCreate(BaseModel):
    """Schema para crear un salario base."""

    rol: RolLiquidacion
    monto: Decimal
    desde: date
    hasta: date | None = None

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def hasta_posterior_a_desde(self) -> "SalarioBaseCreate":
        if self.hasta is not None and self.hasta < self.desde:
            raise ValueError("'hasta' debe ser posterior o igual a 'desde'")
        return self


class SalarioBaseUpdate(BaseModel):
    """Schema para actualizar monto y/o vigencia de cierre."""

    monto: Decimal | None = None
    hasta: date | None = None

    model_config = ConfigDict(extra="forbid")


class SalarioBaseResponse(BaseModel):
    """Schema de respuesta con todos los campos de SalarioBase."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    rol: str
    monto: Decimal
    desde: date
    hasta: date | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, extra="forbid")

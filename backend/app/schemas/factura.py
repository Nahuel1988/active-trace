"""Schemas Pydantic para Factura de docentes monotributistas."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class FacturaCreate(BaseModel):
    """Schema para cargar una factura."""

    usuario_id: uuid.UUID
    periodo: str  # AAAA-MM
    detalle: str
    referencia_archivo: str
    tamano_kb: Decimal

    model_config = ConfigDict(extra="forbid")


class FacturaUpdate(BaseModel):
    """Schema para actualizar una factura Pendiente."""

    detalle: str | None = None
    referencia_archivo: str | None = None
    tamano_kb: Decimal | None = None

    model_config = ConfigDict(extra="forbid")


class FacturaResponse(BaseModel):
    """Schema de respuesta con todos los campos de una Factura."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    usuario_id: uuid.UUID
    periodo: str
    detalle: str
    referencia_archivo: str
    tamano_kb: Decimal
    estado: str
    cargada_at: datetime
    abonada_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, extra="forbid")

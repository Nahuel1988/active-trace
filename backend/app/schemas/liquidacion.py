"""Schemas Pydantic para Liquidacion y cálculo de honorarios."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator


class LiquidacionResponse(BaseModel):
    """Schema de respuesta con todos los campos de una Liquidacion."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    cohorte_id: uuid.UUID
    periodo: str
    usuario_id: uuid.UUID
    rol: str
    comisiones: list[str]
    monto_base: Decimal
    monto_plus: Decimal
    total: Decimal
    es_nexo: bool
    excluido_por_factura: bool
    estado: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, extra="forbid")


class LiquidacionResumen(BaseModel):
    """Resumen de resultado del cálculo de liquidaciones."""

    cantidad_generada: int
    total_general: Decimal
    docentes_omitidos_sin_cbu: int

    model_config = ConfigDict(extra="forbid")


class CalculoRequest(BaseModel):
    """Request para calcular liquidaciones de una cohorte en un período."""

    cohorte_id: uuid.UUID
    periodo: str  # AAAA-MM

    model_config = ConfigDict(extra="forbid")

    @field_validator("periodo")
    @classmethod
    def validar_formato_periodo(cls, v: str) -> str:
        import re
        if not re.match(r"^\d{4}-\d{2}$", v):
            raise ValueError("El período debe tener formato AAAA-MM (ej: 2026-06)")
        return v


class SegmentoLiquidaciones(BaseModel):
    """Segmento de liquidaciones (general, nexo o facturantes)."""

    liquidaciones: list[LiquidacionResponse]
    subtotal: Decimal

    model_config = ConfigDict(extra="forbid")


class KpisLiquidacion(BaseModel):
    """KPIs monetarios globales de la liquidación."""

    total_sin_factura: Decimal
    total_con_factura: Decimal

    model_config = ConfigDict(extra="forbid")


class LiquidacionSegmentadaResponse(BaseModel):
    """Respuesta segmentada de liquidaciones (D6)."""

    segmentos: dict[str, SegmentoLiquidaciones]
    kpis: KpisLiquidacion

    model_config = ConfigDict(extra="forbid")

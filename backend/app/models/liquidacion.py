"""Modelo Liquidacion — registro de honorarios por (docente × cohorte × período)."""

from __future__ import annotations

import enum
import uuid as _uuid

from sqlalchemy import Boolean, ForeignKey, Index, Numeric, String
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, declared_attr, mapped_column

from app.core.database import Base
from app.models.base import TenantScopedMixin


class EstadoLiquidacion(str, enum.Enum):
    """Estados posibles de una liquidación de honorarios."""

    Abierta = "Abierta"
    Cerrada = "Cerrada"


class Liquidacion(TenantScopedMixin, Base):
    """Liquidación de honorarios por docente, cohorte y período mensual.

    Un registro por (usuario_id × cohorte_id × periodo). El cálculo es
    on-demand (D2); recalcular reemplaza registros Abiertos (D5).
    """

    __tablename__ = "liquidacion"

    cohorte_id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cohorte.id", ondelete="CASCADE"),
        nullable=False,
        comment="Cohorte a la que pertenece esta liquidación",
    )
    periodo: Mapped[str] = mapped_column(
        String(7),
        nullable=False,
        comment="Período en formato AAAA-MM (ej: 2026-06)",
    )
    usuario_id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        comment="UUID del docente liquidado",
    )
    rol: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment="Rol del docente en el período",
    )
    comisiones: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        default=list,
        comment="IDs de comisiones del docente en el período",
    )
    monto_base: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=0,
        comment="Monto base según grilla salarial",
    )
    monto_plus: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=0,
        comment="Suma de plus aplicados (una vez por clave, PA-23)",
    )
    total: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=0,
        comment="Total = monto_base + monto_plus",
    )
    es_nexo: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="True si el rol es NEXO (segmentación D6)",
    )
    excluido_por_factura: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="True si el docente es facturador (segmento facturantes, D6)",
    )
    estado: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default=EstadoLiquidacion.Abierta.value,
        comment="Estado: Abierta (recalculable) | Cerrada (inmutable)",
    )

    @declared_attr
    def __table_args__(cls) -> tuple:
        return (
            Index(
                f"ix_{cls.__tablename__}_tenant_cohorte_periodo",
                "tenant_id",
                "cohorte_id",
                "periodo",
            ),
            Index(
                f"ix_{cls.__tablename__}_tenant_usuario_periodo",
                "tenant_id",
                "usuario_id",
                "periodo",
            ),
            Index(
                f"ix_{cls.__tablename__}_tenant_deleted",
                "tenant_id",
                "deleted_at",
            ),
        )

    def __repr__(self) -> str:
        return (
            f"<Liquidacion usuario={self.usuario_id} periodo={self.periodo} "
            f"total={self.total} estado={self.estado}>"
        )

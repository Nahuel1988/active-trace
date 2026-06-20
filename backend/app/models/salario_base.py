"""Modelo SalarioBase — valor base mensual por rol en la grilla salarial."""

from __future__ import annotations

import enum
from datetime import date

from sqlalchemy import Date, Index, Numeric, String
from sqlalchemy.orm import Mapped, declared_attr, mapped_column

from app.core.database import Base
from app.models.base import TenantScopedMixin


class RolLiquidacion(str, enum.Enum):
    """Roles que generan liquidación de honorarios."""

    PROFESOR = "PROFESOR"
    TUTOR = "TUTOR"
    COORDINADOR = "COORDINADOR"
    NEXO = "NEXO"


class SalarioBase(TenantScopedMixin, Base):
    """Salario base mensual por rol con vigencia desde/hasta."""

    __tablename__ = "salario_base"

    rol: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment="Rol docente (PROFESOR, TUTOR, COORDINADOR, NEXO)",
    )
    monto: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        comment="Monto base mensual en la moneda del tenant",
    )
    desde: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Fecha de inicio de vigencia (inclusive)",
    )
    hasta: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        default=None,
        comment="Fecha de fin de vigencia (inclusive); NULL = abierto",
    )

    @declared_attr
    def __table_args__(cls) -> tuple:
        return (
            Index(
                f"ix_{cls.__tablename__}_tenant_rol_vigencia",
                "tenant_id",
                "rol",
                "desde",
                "hasta",
            ),
            Index(
                f"ix_{cls.__tablename__}_tenant_deleted",
                "tenant_id",
                "deleted_at",
            ),
        )

    def __repr__(self) -> str:
        return (
            f"<SalarioBase rol={self.rol} monto={self.monto} "
            f"desde={self.desde} hasta={self.hasta} tenant={self.tenant_id}>"
        )

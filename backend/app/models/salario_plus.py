"""Modelo SalarioPlus — plus salarial por (grupo/clave, rol) con vigencia."""

from __future__ import annotations

from datetime import date

from sqlalchemy import Date, Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, declared_attr, mapped_column

from app.core.database import Base
from app.models.base import TenantScopedMixin


class SalarioPlus(TenantScopedMixin, Base):
    """Plus salarial mensual por (grupo, rol) con vigencia desde/hasta.

    Las 5 claves de grupo (PA-22): PROG, BD, ARQ, MAT, MET.
    Se aplica UNA sola vez por clave por docente por período (PA-23).
    """

    __tablename__ = "salario_plus"

    grupo: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment="Clave del plus (PROG, BD, ARQ, MAT, MET u otras)",
    )
    rol: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment="Rol docente al que aplica este plus",
    )
    descripcion: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Descripción legible del plus salarial",
    )
    monto: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        comment="Monto del plus mensual",
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
                f"ix_{cls.__tablename__}_tenant_grupo_rol_vigencia",
                "tenant_id",
                "grupo",
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
            f"<SalarioPlus grupo={self.grupo} rol={self.rol} "
            f"monto={self.monto} desde={self.desde} tenant={self.tenant_id}>"
        )

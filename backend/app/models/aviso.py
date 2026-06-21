from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
import enum

from app.models.base import TenantScopedMixin
from app.core.database import Base


class AlcanceAviso(str, enum.Enum):
    Global = "global"
    PorMateria = "por_materia"
    PorCohorte = "por_cohorte"
    PorRol = "por_rol"


class SeveridadAviso(str, enum.Enum):
    Info = "info"
    Advertencia = "advertencia"
    Critico = "critico"


class Aviso(Base, TenantScopedMixin):
    __tablename__ = "aviso"

    alcance: Mapped[AlcanceAviso] = mapped_column(
        SQLEnum(AlcanceAviso, name="alcance_aviso", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    materia_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("materia.id", ondelete="SET NULL"), nullable=True
    )
    cohorte_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cohorte.id", ondelete="SET NULL"), nullable=True
    )
    rol_destino: Mapped[str | None] = mapped_column(String(32), nullable=True)
    severidad: Mapped[SeveridadAviso] = mapped_column(
        SQLEnum(SeveridadAviso, name="severidad_aviso", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    titulo: Mapped[str] = mapped_column(String(255), nullable=False)
    cuerpo: Mapped[str] = mapped_column(Text, nullable=False)
    inicio_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    fin_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    orden: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    requiere_ack: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    __table_args__ = (
        Index(
            "ix_aviso_tenant_activo_vigencia",
            "tenant_id",
            "activo",
            "inicio_en",
            "fin_en",
        ),
    )

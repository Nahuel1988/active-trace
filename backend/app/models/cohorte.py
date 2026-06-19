from __future__ import annotations

import uuid
from sqlalchemy import String, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
import enum

from app.models.base import TenantScopedMixin
from app.core.database import Base


class EstadoCohorte(str, enum.Enum):
    Activa = "activa"
    Inactiva = "inactiva"


class Cohorte(Base, TenantScopedMixin):
    __tablename__ = "cohorte"

    carrera_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("carrera.id", ondelete="CASCADE"), nullable=False
    )
    nombre: Mapped[str] = mapped_column(String(128), nullable=False)
    anio: Mapped[int] = mapped_column(Integer, nullable=False)
    vig_desde: Mapped[str] = mapped_column(String(20), nullable=False)
    vig_hasta: Mapped[str | None] = mapped_column(String(20), nullable=True)
    estado: Mapped[str] = mapped_column(String(16), nullable=False, default=EstadoCohorte.Activa)

    __table_args__ = (
        UniqueConstraint("tenant_id", "carrera_id", "nombre", name="uq_cohorte_tenant_carrera_nombre"),
    )

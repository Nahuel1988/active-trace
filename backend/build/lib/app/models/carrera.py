from __future__ import annotations

from sqlalchemy import Column, String, UniqueConstraint
from sqlalchemy import Enum as SQLEnum
import enum
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TenantScopedMixin
from app.core.database import Base


class EstadoCarrera(str, enum.Enum):
    Activa = "activa"
    Inactiva = "inactiva"


class Carrera(Base, TenantScopedMixin):
    __tablename__ = "carrera"

    codigo: Mapped[str] = mapped_column(String(64), nullable=False)
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    estado: Mapped[EstadoCarrera] = mapped_column(SQLEnum(EstadoCarrera, name="estado_carrera"), nullable=False, default=EstadoCarrera.Activa)

    __table_args__ = (
        UniqueConstraint("tenant_id", "codigo", name="uq_carrera_tenant_codigo"),
    )

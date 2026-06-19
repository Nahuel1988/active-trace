from __future__ import annotations

from sqlalchemy import String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TenantScopedMixin
from app.core.database import Base
import enum


class EstadoMateria(str, enum.Enum):
    Activa = "activa"
    Inactiva = "inactiva"


class Materia(Base, TenantScopedMixin):
    __tablename__ = "materia"

    codigo: Mapped[str] = mapped_column(String(64), nullable=False)
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    from sqlalchemy import String as _String
    estado: Mapped[EstadoMateria] = mapped_column(_String(16), nullable=False, default=EstadoMateria.Activa)

    __table_args__ = (
        UniqueConstraint("tenant_id", "codigo", name="uq_materia_tenant_codigo"),
    )

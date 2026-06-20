"""Modelo Guardia — registro de guardia de atención por tutor.

Cada guardia se vincula a una asignacion (TUTOR que la cubre), materia,
carrera y cohorte. Ciclo de estados: Pendiente → Realizada | Cancelada.
Realizada es terminal; Cancelada puede revertirse a Pendiente solo por
COORDINADOR/ADMIN (D-05).
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
import enum

from app.core.database import Base
from app.models.base import TenantScopedMixin
from app.models.slot_encuentro import DiaSemana


class EstadoGuardia(str, enum.Enum):
    """Estados del ciclo de vida de una guardia."""

    pendiente = "pendiente"
    realizada = "realizada"
    cancelada = "cancelada"


class Guardia(TenantScopedMixin, Base):
    """Registro de guardia de atención cubierta por un tutor."""

    __tablename__ = "guardia"

    asignacion_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("asignacion.id", ondelete="CASCADE"),
        nullable=False,
        comment="FK → asignacion.id (tutor que cubre la guardia)",
    )
    materia_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("materia.id", ondelete="CASCADE"),
        nullable=False,
        comment="FK → materia.id",
    )
    carrera_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("carrera.id", ondelete="CASCADE"),
        nullable=False,
        comment="FK → carrera.id",
    )
    cohorte_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cohorte.id", ondelete="CASCADE"),
        nullable=False,
        comment="FK → cohorte.id",
    )
    dia: Mapped[DiaSemana] = mapped_column(
        nullable=False,
        comment="Día de la semana (lunes … domingo)",
    )
    horario: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Rango horario (ej. '14:00–15:00')",
    )
    estado: Mapped[EstadoGuardia] = mapped_column(
        nullable=False,
        default=EstadoGuardia.pendiente,
        comment="Pendiente | Realizada | Cancelada",
    )
    comentarios: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default=None,
        comment="Comentarios opcionales sobre la guardia",
    )
    creada_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Timestamp de creación (para ordenamiento y export)",
    )

    __table_args__ = (
        Index("ix_guardia_tenant_asignacion", "tenant_id", "asignacion_id"),
        Index("ix_guardia_tenant_materia", "tenant_id", "materia_id"),
        Index("ix_guardia_tenant_estado", "tenant_id", "estado"),
    )

"""Modelo InstanciaEncuentro — encuentro concreto derivado de un slot.

Cada instancia tiene un ciclo de vida independiente del slot padre (RN-14).
Se crean automáticamente al crear el slot (en el service, no en el ORM).
El slot puede soft-deletearse sin afectar las instancias existentes.

Estados: Programado → Realizado | Cancelado (ver D-04).
Reversiones solo COORDINADOR/ADMIN.
"""

from __future__ import annotations

import uuid
from datetime import date, time

from sqlalchemy import ForeignKey, Index, Text, Time
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.core.database import Base
from app.models.base import TenantScopedMixin


class EstadoInstancia(str, enum.Enum):
    """Estados del ciclo de vida de una instancia de encuentro."""

    programado = "programado"
    realizado = "realizado"
    cancelado = "cancelado"


class InstanciaEncuentro(TenantScopedMixin, Base):
    """Instancia concreta de un encuentro (derivada de slot o independiente)."""

    __tablename__ = "instancia_encuentro"

    slot_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("slot_encuentro.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
        comment="FK → slot_encuentro.id (NULL si la instancia es independiente)",
    )
    materia_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("materia.id", ondelete="CASCADE"),
        nullable=False,
        comment="FK → materia.id (contexto académico desnormalizado)",
    )
    fecha: Mapped[date] = mapped_column(
        nullable=False,
        comment="Fecha del encuentro",
    )
    hora: Mapped[time] = mapped_column(
        Time(timezone=False),
        nullable=False,
        comment="Hora del encuentro",
    )
    titulo: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Título del encuentro (copia del slot al generarse)",
    )
    estado: Mapped[EstadoInstancia] = mapped_column(
        nullable=False,
        default=EstadoInstancia.programado,
        comment="Programado | Realizado | Cancelado",
    )
    meet_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default=None,
        comment="URL de videoconferencia (puede diferir del slot)",
    )
    video_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default=None,
        comment="URL de grabación (suele agregarse tras Realizado)",
    )
    comentario: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default=None,
        comment="Comentario del docente sobre la instancia",
    )

    # Relación muchos-a-uno con slot (back_populates)
    slot_rel: Mapped["SlotEncuentro | None"] = relationship(
        "SlotEncuentro",
        back_populates="instancias",
        lazy="select",
        viewonly=True,
    )

    __table_args__ = (
        Index("ix_instancia_encuentro_tenant_slot", "tenant_id", "slot_id"),
        Index("ix_instancia_encuentro_tenant_materia", "tenant_id", "materia_id"),
        Index("ix_instancia_encuentro_tenant_estado", "tenant_id", "estado"),
        Index("ix_instancia_encuentro_tenant_fecha", "tenant_id", "fecha"),
    )

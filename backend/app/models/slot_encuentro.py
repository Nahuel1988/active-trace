"""Modelo SlotEncuentro — plantilla recurrente o fecha única de encuentro.

Un slot puede ser:
- Recurrente: ``cant_semanas ≥ 1``, ``fecha_unica = NULL``. El service genera
  N instancias (una por semana) a partir de ``fecha_inicio``.
- Único: ``cant_semanas = 0``, ``fecha_unica`` no nula. Se genera exactamente
  1 instancia.

FK a ``asignacion`` (quién crea / es responsable) y ``materia`` (contexto
académico desnormalizado para evitar joins en listados).
"""

import uuid
from datetime import date, time

from sqlalchemy import ForeignKey, Index, Text, Time, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, relationship
import enum

from app.core.database import Base
from app.models.base import TenantScopedMixin


class DiaSemana(str, enum.Enum):
    """Días de la semana para slots y guardias."""

    lunes = "lunes"
    martes = "martes"
    miercoles = "miercoles"
    jueves = "jueves"
    viernes = "viernes"
    sabado = "sabado"
    domingo = "domingo"


class SlotEncuentro(TenantScopedMixin, Base):
    """Plantilla de encuentro (recurrente o único)."""

    __tablename__ = "slot_encuentro"

    asignacion_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("asignacion.id", ondelete="CASCADE"),
        nullable=False,
        comment="FK → asignacion.id (quién dicta el encuentro)",
    )
    materia_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("materia.id", ondelete="CASCADE"),
        nullable=False,
        comment="FK → materia.id (contexto académico desnormalizado)",
    )
    titulo: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Título del encuentro (ej. 'Clase 1: Introducción')",
    )
    hora: Mapped[time] = mapped_column(
        Time(timezone=False),
        nullable=False,
        comment="Hora del encuentro (sin timezone, ej. 18:00)",
    )
    dia_semana: Mapped[DiaSemana] = mapped_column(
        nullable=False,
        comment="Día de la semana (lunes … domingo)",
    )
    fecha_inicio: Mapped[date] = mapped_column(
        nullable=False,
        comment="Fecha del primer encuentro (el día debe coincidir con dia_semana)",
    )
    cant_semanas: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="0 = único; ≥1 = recurrente (N instancias generadas)",
    )
    fecha_unica: Mapped[date | None] = mapped_column(
        nullable=True,
        default=None,
        comment="Fecha concreta si es único (modo unico); NULL si recurrente",
    )
    meet_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default=None,
        comment="URL de videoconferencia (opcional, puede editarse en instancias)",
    )
    vig_desde: Mapped[date] = mapped_column(
        nullable=False,
        comment="Inicio de vigencia del slot",
    )
    vig_hasta: Mapped[date | None] = mapped_column(
        nullable=True,
        default=None,
        comment="Fin de vigencia del slot (NULL = indefinida)",
    )

    # Relación uno-a-muchos con instancias (cargada vía joinedload en repos)
    instancias: Mapped[list["InstanciaEncuentro"]] = relationship(
        "InstanciaEncuentro",
        back_populates="slot_rel",
        lazy="select",
        viewonly=True,
    )

    @declared_attr
    def __table_args__(cls) -> tuple:
        return (
            Index(
                "ix_slot_encuentro_tenant_materia",
                "tenant_id",
                "materia_id",
            ),
            Index(
                "ix_slot_encuentro_tenant_asignacion",
                "tenant_id",
                "asignacion_id",
            ),
        )

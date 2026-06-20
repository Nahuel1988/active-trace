"""Modelos Calificacion y UmbralMateria — calificaciones y umbral de aprobación.

Calificacion almacena notas numéricas y textuales de alumnos en actividades.
UmbralMateria almacena el criterio de aprobación por asignación docente.

``aprobado`` NO se almacena — se deriva en read-time (D-01).
"""

from __future__ import annotations

import enum
import uuid as _uuid

from sqlalchemy import (
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, declared_attr, mapped_column

from app.core.database import Base
from app.models.base import TenantScopedMixin


class OrigenCalificacionDB(str, enum.Enum):
    """Origen de una calificación en la BD."""

    IMPORTADO = "importado"
    MANUAL = "manual"


class Calificacion(TenantScopedMixin, Base):
    """Calificación de un alumno en una actividad.

    ``aprobado`` NO es columna persistida — se computa en read-time
    al cruzar ``nota_numerica >= UmbralMateria.umbral_pct`` o
    ``nota_textual in UmbralMateria.valores_aprobatorios``.

    ``deleted_by`` almacena el UUID del usuario que realizó el soft-delete
    (vaciado), permitiendo trazar quién eliminó los registros.

    FK a ``entrada_padron.id`` (C-09), ``materia.id`` (C-06),
    ``user.id`` (C-03) via ``creado_por``.
    """

    __tablename__ = "calificacion"

    entrada_padron_id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("entrada_padron.id", ondelete="CASCADE"),
        nullable=False,
        comment="FK → EntradaPadron (alumno)",
    )
    materia_id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("materia.id", ondelete="CASCADE"),
        nullable=False,
        comment="FK → Materia",
    )
    actividad: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Nombre de la actividad (ej: TP1, Examen Parcial)",
    )
    nota_numerica: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="Nota numérica (nullable — puede ser solo textual)",
    )
    nota_textual: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Nota textual (nullable — puede ser solo numérica)",
    )
    origen: Mapped[OrigenCalificacionDB] = mapped_column(
        Enum(OrigenCalificacionDB, name="origen_calificacion", create_constraint=True),
        nullable=False,
        default=OrigenCalificacionDB.IMPORTADO,
        comment="Origen: importado (archivo) o manual",
    )
    creado_por: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="SET NULL"),
        nullable=False,
        comment="FK → User que importó/creó la calificación",
    )
    deleted_by: Mapped[_uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="UUID del usuario que realizó el soft-delete (vaciado)",
    )

    @declared_attr
    def __table_args__(cls) -> tuple:
        return (
            Index(
                f"ix_{cls.__tablename__}_tenant_materia_creador",
                "tenant_id",
                "materia_id",
                "creado_por",
            ),
            Index(
                f"ix_{cls.__tablename__}_tenant_entrada",
                "tenant_id",
                "entrada_padron_id",
            ),
            Index(
                f"ix_{cls.__tablename__}_tenant_deleted",
                "tenant_id",
                "deleted_at",
            ),
        )

    def __repr__(self) -> str:
        return (
            f"<Calificacion id={self.id} actividad={self.actividad} "
            f"materia={self.materia_id} entrada={self.entrada_padron_id} "
            f"origen={self.origen.value} tenant={self.tenant_id}>"
        )


class UmbralMateria(TenantScopedMixin, Base):
    """Umbral de aprobación configurable por asignación docente.

    Cada docente tiene su propio umbral para la misma materia (D-02).
    ``umbral_pct`` default = 60 (RN-03).
    ``valores_aprobatorios`` es JSONB con lista de valores textuales
    que cuentan como aprobado (ej: ["Satisfactorio", "Supera lo esperado"]).

    UniqueConstraint(tenant_id, asignacion_id, materia_id) garantiza
    un solo umbral por combinación.
    """

    __tablename__ = "umbral_materia"

    asignacion_id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("asignacion.id", ondelete="CASCADE"),
        nullable=False,
        comment="FK → Asignacion (docente × materia)",
    )
    materia_id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("materia.id", ondelete="CASCADE"),
        nullable=False,
        comment="FK → Materia",
    )
    umbral_pct: Mapped[int] = mapped_column(
        Integer,
        default=60,
        nullable=False,
        comment="Porcentaje mínimo para aprobar (default 60)",
    )
    valores_aprobatorios: Mapped[list[str] | None] = mapped_column(
        JSONB,
        nullable=True,
        default=None,
        comment="Lista de valores textuales que cuentan como aprobado",
    )

    @declared_attr
    def __table_args__(cls) -> tuple:
        return (
            UniqueConstraint(
                "tenant_id",
                "asignacion_id",
                "materia_id",
                name=f"uq_{cls.__tablename__}_tenant_asignacion_materia",
            ),
            Index(
                f"ix_{cls.__tablename__}_tenant_asignacion",
                "tenant_id",
                "asignacion_id",
            ),
            Index(
                f"ix_{cls.__tablename__}_tenant_deleted",
                "tenant_id",
                "deleted_at",
            ),
        )

    def __repr__(self) -> str:
        return (
            f"<UmbralMateria id={self.id} asignacion={self.asignacion_id} "
            f"materia={self.materia_id} umbral_pct={self.umbral_pct} "
            f"tenant={self.tenant_id}>"
        )

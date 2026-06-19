"""Modelo Tarea — tarea interna con doble trazabilidad de actor y máquina de estados.

Una Tarea representa un item de trabajo docente: un COORDINADOR asigna a un
PROFESOR/TUTOR, con seguimiento de estado y posibilidad de delegación.
"""

from __future__ import annotations

import uuid as _uuid

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, relationship

from app.core.database import Base
from app.models.base import TenantScopedMixin

import enum


class EstadoTarea(str, enum.Enum):
    """Estados posibles de una tarea interna.

    Pendiente → EnProgreso | Cancelada
    EnProgreso → Resuelta | Cancelada | Pendiente
    Resuelta → EnProgreso (reapertura, solo COORDINADOR/ADMIN)
    Cancelada → (terminal)
    """

    Pendiente = "Pendiente"
    EnProgreso = "EnProgreso"
    Resuelta = "Resuelta"
    Cancelada = "Cancelada"


class Tarea(TenantScopedMixin, Base):
    """Tarea interna con trazabilidad de quién asigna y quién resuelve."""

    __tablename__ = "tarea"

    descripcion: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Descripción de la tarea",
    )
    estado: Mapped[EstadoTarea] = mapped_column(
        String(32),
        nullable=False,
        default=EstadoTarea.Pendiente,
        comment="Estado actual de la tarea (Pendiente/EnProgreso/Resuelta/Cancelada)",
    )
    asignado_a: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        comment="UUID del usuario asignado a resolver la tarea",
    )
    asignado_por: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        comment="UUID del usuario que asignó o delegó la tarea",
    )
    materia_id: Mapped[_uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("materia.id", ondelete="SET NULL"),
        nullable=True,
        comment="UUID de la materia asociada (opcional, tarea institucional si null)",
    )
    contexto_id: Mapped[_uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="UUID de referencia genérica a otra entidad del dominio (sin FK formal)",
    )

    # -- Relationships (para consultas ORM, no obligatorias para repos) --
    asignado_a_user = relationship(
        "User", foreign_keys=[asignado_a], lazy="selectin"
    )
    asignado_por_user = relationship(
        "User", foreign_keys=[asignado_por], lazy="selectin"
    )

    @declared_attr
    def __table_args__(cls) -> tuple:
        return (
            # Índices de filtro (D-05): tenant + columna de filtro
            Index(
                f"ix_{cls.__tablename__}_tenant_asignado_a",
                "tenant_id",
                "asignado_a",
            ),
            Index(
                f"ix_{cls.__tablename__}_tenant_asignado_por",
                "tenant_id",
                "asignado_por",
            ),
            Index(
                f"ix_{cls.__tablename__}_tenant_materia_id",
                "tenant_id",
                "materia_id",
            ),
            Index(
                f"ix_{cls.__tablename__}_tenant_estado",
                "tenant_id",
                "estado",
            ),
            # Índice por defecto del mixin (tenant_id, deleted_at)
            Index(
                f"ix_{cls.__tablename__}_tenant_deleted",
                "tenant_id",
                "deleted_at",
            ),
        )

    def __repr__(self) -> str:
        return (
            f"<Tarea id={self.id} estado={self.estado} "
            f"asignado_a={self.asignado_a} tenant={self.tenant_id}>"
        )

"""Modelo ComentarioTarea — hilo de comentarios append-only por tarea.

Append-only: una vez creado, un comentario no se edita ni se borra.
NO tiene updated_at ni deleted_at (es inmutable por diseño).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ComentarioTarea(Base):
    """Comentario en el hilo de una tarea. Append-only: no se edita ni borra.

    Attributes:
        id: UUID v4, PK.
        tenant_id: UUID, FK → tenant.id.
        tarea_id: UUID, FK → tarea.id.
        autor_id: UUID, FK → user.id (quien escribió el comentario).
        texto: Contenido del comentario.
        creado_at: Timestamp UTC de creación (inmutable).
    """

    __tablename__ = "comentario_tarea"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenant.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tarea_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tarea.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    autor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
    )
    texto: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Contenido del comentario",
    )
    creado_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_comentario_tarea_tenant_tarea", "tenant_id", "tarea_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<ComentarioTarea id={self.id} "
            f"tarea_id={self.tarea_id} autor_id={self.autor_id}>"
        )

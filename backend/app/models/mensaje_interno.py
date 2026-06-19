"""Modelo MensajeInterno — cada mensaje dentro de un HiloMensaje (C-20).

Multi-tenant: tenant_id obligatorio; soft delete vía deleted_at.
leido_at: NULL = no leído; timestamp = leído (por el destinatario del hilo).
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Index, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, declared_attr, mapped_column

from app.core.database import Base
from app.models.base import TenantScopedMixin


class MensajeInterno(TenantScopedMixin, Base):
    """Mensaje individual dentro de un hilo de conversación interna."""

    __tablename__ = "mensaje_interno"

    # Hilo al que pertenece
    hilo_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        comment="FK al HiloMensaje al que pertenece este mensaje",
    )

    # Autor (SIEMPRE tomado del JWT en el service, nunca del body)
    autor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        comment="FK al User autor del mensaje (tomado del JWT)",
    )

    # Contenido
    cuerpo: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Cuerpo del mensaje en texto plano",
    )

    # Timestamps específicos del mensaje
    creado_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Timestamp de creación del mensaje",
    )

    # Estado de lectura — NULL = no leído, timestamp = leído
    leido_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        comment="Timestamp de lectura; NULL si no leído aún",
    )

    @declared_attr
    def __table_args__(cls) -> tuple:
        return (
            Index(
                f"ix_{cls.__tablename__}_tenant_hilo",
                "tenant_id",
                "hilo_id",
            ),
            Index(
                f"ix_{cls.__tablename__}_tenant_deleted",
                "tenant_id",
                "deleted_at",
            ),
        )

    def __repr__(self) -> str:
        return (
            f"<MensajeInterno id={self.id} hilo={self.hilo_id} "
            f"autor={self.autor_id} leido_at={self.leido_at}>"
        )

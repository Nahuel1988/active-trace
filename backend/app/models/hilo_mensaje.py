"""Modelo HiloMensaje — conversación entre dos usuarios del tenant (C-20).

Una conversación bidireccional (1-a-1) entre iniciado_por y destinatario_id.
La pertenencia se evalúa como: user.id in {iniciado_por, destinatario_id}.

Multi-tenant: tenant_id obligatorio; soft delete vía deleted_at.
"""

import uuid

from sqlalchemy import Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, declared_attr, mapped_column

from app.core.database import Base
from app.models.base import TenantScopedMixin


class HiloMensaje(TenantScopedMixin, Base):
    """Conversación interna entre dos usuarios del tenant."""

    __tablename__ = "hilo_mensaje"

    # Asunto del hilo
    asunto: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Asunto o título del hilo de conversación",
    )

    # Participantes
    iniciado_por: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        comment="FK al User que inició el hilo (SIEMPRE del JWT, nunca del body)",
    )
    destinatario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        comment="FK al User destinatario del hilo",
    )

    @declared_attr
    def __table_args__(cls) -> tuple:
        return (
            Index(
                f"ix_{cls.__tablename__}_tenant_destinatario",
                "tenant_id",
                "destinatario_id",
            ),
            Index(
                f"ix_{cls.__tablename__}_tenant_deleted",
                "tenant_id",
                "deleted_at",
            ),
            Index(
                f"ix_{cls.__tablename__}_tenant_iniciado_por",
                "tenant_id",
                "iniciado_por",
            ),
        )

    def __repr__(self) -> str:
        return (
            f"<HiloMensaje id={self.id} tenant={self.tenant_id} "
            f"asunto={self.asunto!r}>"
        )

from __future__ import annotations

import uuid as _uuid

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, declared_attr, mapped_column

from app.core.database import Base
from app.models.base import TenantScopedMixin

import enum


class EstadoComunicacion(str, enum.Enum):
    Pendiente = "Pendiente"
    Enviando = "Enviando"
    Enviado = "Enviado"
    Error = "Error"
    Cancelado = "Cancelado"


class Comunicacion(TenantScopedMixin, Base):
    __tablename__ = "comunicacion"

    enviado_por: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
    )
    materia_id: Mapped[_uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("materia.id", ondelete="SET NULL"),
        nullable=True,
    )
    destinatario: Mapped[str] = mapped_column(Text, nullable=False)
    destinatario_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )
    asunto: Mapped[str] = mapped_column(Text, nullable=False)
    cuerpo: Mapped[str] = mapped_column(Text, nullable=False)
    estado: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=EstadoComunicacion.Pendiente.value,
    )
    lote_id: Mapped[_uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    requiere_aprobacion: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    enviado_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    @declared_attr
    def __table_args__(cls) -> tuple:
        return (
            Index(
                f"ix_{cls.__tablename__}_tenant_lote",
                "tenant_id",
                "lote_id",
            ),
            Index(
                f"ix_{cls.__tablename__}_tenant_estado",
                "tenant_id",
                "estado",
            ),
            Index(
                f"ix_{cls.__tablename__}_tenant_enviado_por",
                "tenant_id",
                "enviado_por",
            ),
            Index(
                f"ix_{cls.__tablename__}_tenant_destinatario_hash",
                "tenant_id",
                "destinatario_hash",
            ),
            Index(
                f"ix_{cls.__tablename__}_tenant_deleted",
                "tenant_id",
                "deleted_at",
            ),
        )

    def __repr__(self) -> str:
        return (
            f"<Comunicacion id={self.id} estado={self.estado} "
            f"lote_id={self.lote_id} tenant={self.tenant_id}>"
        )

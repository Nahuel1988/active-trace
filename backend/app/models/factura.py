"""Modelo Factura — comprobante de monotributista asociado a un período."""

from __future__ import annotations

import enum
import uuid as _uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, declared_attr, mapped_column

from app.core.database import Base
from app.models.base import TenantScopedMixin


class EstadoFactura(str, enum.Enum):
    """Estados de una factura de monotributista."""

    Pendiente = "Pendiente"
    Abonada = "Abonada"


class Factura(TenantScopedMixin, Base):
    """Factura de docente facturador con transición Pendiente → Abonada (D7)."""

    __tablename__ = "factura"

    usuario_id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        comment="UUID del docente facturador",
    )
    periodo: Mapped[str] = mapped_column(
        String(7),
        nullable=False,
        comment="Período en formato AAAA-MM",
    )
    detalle: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Descripción del servicio facturado",
    )
    referencia_archivo: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
        comment="Nombre o path del archivo adjunto (almacenamiento externo)",
    )
    tamano_kb: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="Tamaño del archivo en KB",
    )
    estado: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default=EstadoFactura.Pendiente.value,
        comment="Estado: Pendiente | Abonada",
    )
    cargada_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Timestamp de carga de la factura",
    )
    abonada_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        comment="Timestamp de pago; NULL si Pendiente",
    )

    @declared_attr
    def __table_args__(cls) -> tuple:
        return (
            Index(
                f"ix_{cls.__tablename__}_tenant_periodo",
                "tenant_id",
                "periodo",
            ),
            Index(
                f"ix_{cls.__tablename__}_tenant_usuario_periodo",
                "tenant_id",
                "usuario_id",
                "periodo",
            ),
            Index(
                f"ix_{cls.__tablename__}_tenant_deleted",
                "tenant_id",
                "deleted_at",
            ),
        )

    def __repr__(self) -> str:
        return (
            f"<Factura usuario={self.usuario_id} periodo={self.periodo} "
            f"estado={self.estado}>"
        )

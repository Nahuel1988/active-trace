from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AcknowledgmentAviso(Base):
    """Registro de confirmación de lectura de un aviso por un usuario.
    
    Append-only: no tiene updated_at ni deleted_at. 
    UniqueConstraint(tenant_id, aviso_id, usuario_id) garantiza idempotencia.
    """

    __tablename__ = "acknowledgment_aviso"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenant.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    aviso_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("aviso.id", ondelete="CASCADE"),
        nullable=False,
    )
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
    )
    confirmado_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "aviso_id",
            "usuario_id",
            name="uq_ack_aviso_tenant_usuario",
        ),
    )

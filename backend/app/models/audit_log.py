"""Modelo AuditLog — registro inmutable de auditoría append-only.

Este modelo NO hereda de ``TenantScopedMixin`` porque:
- No tiene ``updated_at`` (inmutable por diseño — no se actualiza nunca).
- No tiene ``deleted_at`` (inmutable — no se elimina nunca).

La inmutabilidad se refuerza a nivel de base de datos con reglas PostgreSQL
``ON UPDATE DO INSTEAD NOTHING`` y ``ON DELETE DO INSTEAD NOTHING`` en la
migración 004.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AuditLog(Base):
    """Registro de auditoría append-only.

    Cada fila representa una acción de dominio ejecutada por un actor
    sobre una entidad del sistema. Inmutable: no se modifica ni elimina.

    Attributes:
        id: UUID v4, PK.
        tenant_id: UUID, FK → tenant.id.
        fecha_hora: Timestamp UTC de cuando ocurrió la acción.
        actor_id: UUID, FK → user.id (quien ejecutó la acción).
        impersonado_id: UUID nullable, FK → user.id (usuario impersonado,
            si la acción ocurrió bajo impersonación).
        materia_id: UUID nullable (FK futura → materia.id).
        accion: Código de acción (ej: ``CALIFICACIONES_IMPORTAR``).
        detalle: JSONB con datos contextuales de la acción.
        filas_afectadas: Cantidad de registros afectados (0 si N/A).
        ip: Dirección IP del cliente que originó la acción.
        user_agent: User-Agent del cliente.
    """

    __tablename__ = "audit_log"

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
    fecha_hora: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    actor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
    )
    impersonado_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="SET NULL"),
        nullable=True,
    )
    materia_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="FK futura → materia.id (tabla aún no creada)",
    )
    accion: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Código de acción (ej: CALIFICACIONES_IMPORTAR)",
    )
    detalle: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )
    filas_afectadas: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    ip: Mapped[str] = mapped_column(
        String(45),
        nullable=False,
        comment="Dirección IP del cliente (IPv4 o IPv6)",
    )
    user_agent: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
        comment="User-Agent del cliente",
    )

    __table_args__ = (
        Index("ix_audit_log_tenant_fecha", "tenant_id", "fecha_hora"),
    )

    def __repr__(self) -> str:
        return (
            f"<AuditLog id={self.id} tenant={self.tenant_id} "
            f"accion='{self.accion}'>"
        )

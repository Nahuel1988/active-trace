"""Modelo TotpSecret — secreto TOTP para autenticación de dos factores.

El secreto se almacena cifrado AES-256 en `secret_encrypted`.
La columna `confirmed_at` indica cuándo el usuario confirmó la configuración 2FA.
Un usuario puede tener a lo sumo un secreto TOTP activo (UNIQUE user_id).
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, declared_attr, mapped_column

from app.core.database import Base
from app.models.base import TenantScopedMixin


class TotpSecret(TenantScopedMixin, Base):
    __tablename__ = "totp_secret"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        comment="FK única: un usuario solo puede tener un secreto TOTP activo",
    )
    secret_encrypted: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Secreto TOTP cifrado AES-256-GCM (nunca en claro)",
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        comment="Momento en que el usuario confirmó la configuración 2FA",
    )

    @declared_attr
    def __table_args__(cls) -> tuple:
        return (
            Index(
                f"ix_{cls.__tablename__}_tenant_deleted",
                "tenant_id",
                "deleted_at",
            ),
        )

    def __repr__(self) -> str:
        return f"<TotpSecret id={self.id} user={self.user_id} confirmed={self.confirmed_at is not None}>"

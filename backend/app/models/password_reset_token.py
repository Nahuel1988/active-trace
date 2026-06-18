"""Modelo PasswordResetToken — tokens de reseteo de contraseña.

Solo se persiste el hash del token, nunca el token en claro.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, declared_attr, mapped_column

from app.core.database import Base
from app.models.base import TenantScopedMixin


class PasswordResetToken(TenantScopedMixin, Base):
    __tablename__ = "password_reset_token"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token_hash: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        comment="SHA-256 del token de reseteo (nunca el token en claro)",
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        comment="Momento de uso del token; NULL = no usado aún",
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
        return f"<PasswordResetToken id={self.id} user={self.user_id}>"

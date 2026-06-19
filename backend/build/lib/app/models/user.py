"""Modelo User — identidad de usuario multi-tenant.

PII sensible (email) se almacena cifrado AES-256 en `email_encrypted`.
La columna `email_lookup` contiene un HMAC determinístico para búsqueda
por email sin descifrar.
"""

import uuid

from sqlalchemy import Boolean, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, declared_attr, mapped_column

from app.core.database import Base
from app.models.base import TenantScopedMixin


class User(TenantScopedMixin, Base):
    __tablename__ = "user"

    email_encrypted: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Email cifrado AES-256-GCM (ciphertext en base64)",
    )
    email_lookup: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        comment="HMAC determinístico del email para búsqueda única",
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Hash Argon2id de la contraseña",
    )
    legajo: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Legajo del alumno (atributo de negocio, NO credencial)",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    totp_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    @declared_attr
    def __table_args__(cls) -> tuple:
        return (
            UniqueConstraint(
                "tenant_id",
                "email_lookup",
                name=f"uq_{cls.__tablename__}_tenant_email",
            ),
            Index(
                f"ix_{cls.__tablename__}_tenant_deleted",
                "tenant_id",
                "deleted_at",
            ),
        )

    def __repr__(self) -> str:
        return f"<User id={self.id} tenant={self.tenant_id} active={self.is_active}>"

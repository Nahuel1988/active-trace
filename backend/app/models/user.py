"""Modelo User — identidad de usuario multi-tenant.

PII sensible (email, dni, cuil, cbu, alias_cbu) se almacena cifrado AES-256-GCM
en columnas `*_encrypted`. La columna `email_lookup` contiene un HMAC
determinístico para búsqueda por email sin descifrar.

C-07 extiende el modelo con atributos institucionales:
    nombre, apellidos, banco, regional, legajo_profesional, facturador
y columnas PII cifradas:
    dni_encrypted, cuil_encrypted, cbu_encrypted, alias_cbu_encrypted

Todas las nuevas columnas son NULLABLE para convivir con usuarios pre-existentes
creados en C-02.
"""

import uuid
from typing import Literal

from sqlalchemy import Boolean, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, declared_attr, mapped_column

from app.core.database import Base
from app.models.base import TenantScopedMixin


class User(TenantScopedMixin, Base):
    __tablename__ = "user"

    # -----------------------------------------------------------------------
    # Credenciales y email (C-02)
    # -----------------------------------------------------------------------
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

    # -----------------------------------------------------------------------
    # Atributos institucionales (C-07) — NULLABLE para convivencia con C-02
    # -----------------------------------------------------------------------
    nombre: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Nombre/s del usuario",
    )
    apellidos: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Apellido/s del usuario",
    )
    banco: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Banco del usuario (texto plano, no es PII regulada)",
    )
    regional: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Regional / sede del usuario",
    )
    legajo_profesional: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Legajo profesional (atributo de negocio, NO credencial)",
    )
    facturador: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        comment="True si el usuario emite facturas",
    )

    # -----------------------------------------------------------------------
    # PII cifrada (C-07) — AES-256-GCM vía encryption_service
    # -----------------------------------------------------------------------
    dni_encrypted: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="DNI cifrado AES-256-GCM (ciphertext en base64)",
    )
    cuil_encrypted: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="CUIL cifrado AES-256-GCM (ciphertext en base64)",
    )
    cbu_encrypted: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="CBU cifrado AES-256-GCM (ciphertext en base64)",
    )
    alias_cbu_encrypted: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Alias CBU cifrado AES-256-GCM (ciphertext en base64)",
    )

    # -----------------------------------------------------------------------
    # Modalidad de cobro (C-20) — NULLABLE para convivencia con usuarios pre-existentes
    # -----------------------------------------------------------------------
    modalidad_cobro: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="Modalidad de cobro: 'factura' o 'liquidacion'",
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

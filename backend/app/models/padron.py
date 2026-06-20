"""Modelos VersionPadron y EntradaPadron — padrón versionado de alumnos.

Cada carga genera una nueva VersionPadron. Solo puede haber una versión
activa por combinación (tenant_id, materia_id, cohorte_id).

EntradaPadron.email se almacena cifrado AES-256-GCM (PII).
usuario_id es nullable: un alumno puede estar en el padrón sin tener cuenta.
"""

from __future__ import annotations

import uuid as _uuid

from sqlalchemy import ForeignKey, Index, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, declared_attr, mapped_column

from app.core.database import Base
from app.models.base import TenantScopedMixin


class VersionPadron(TenantScopedMixin, Base):
    """Versión de padrón para una combinación materia × cohorte.

    Al activar una nueva versión, la anterior se desactiva (activa = false).
    El historial de versiones se conserva para auditoría.
    """

    __tablename__ = "version_padron"

    materia_id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("materia.id", ondelete="CASCADE"),
        nullable=False,
        comment="UUID de la materia",
    )
    cohorte_id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cohorte.id", ondelete="CASCADE"),
        nullable=False,
        comment="UUID de la cohorte",
    )
    activa: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
        comment="True si es la versión activa para la tupla (materia, cohorte)",
    )
    total_entradas: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Cantidad de entradas de padrón en esta versión",
    )
    origen: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Origen de la carga: 'archivo' | 'moodle' | 'manual'",
    )

    @declared_attr
    def __table_args__(cls) -> tuple:
        return (
            # Invariante D-01: una sola versión activa por (tenant, materia, cohorte)
            Index(
                f"uq_{cls.__tablename__}_activa_por_tupla",
                "tenant_id",
                "materia_id",
                "cohorte_id",
                unique=True,
                postgresql_where=text("activa = true"),
            ),
            Index(
                f"ix_{cls.__tablename__}_tenant_materia_cohorte",
                "tenant_id",
                "materia_id",
                "cohorte_id",
            ),
            Index(
                f"ix_{cls.__tablename__}_tenant_deleted",
                "tenant_id",
                "deleted_at",
            ),
        )

    def __repr__(self) -> str:
        return (
            f"<VersionPadron id={self.id} materia={self.materia_id} "
            f"cohorte={self.cohorte_id} activa={self.activa} "
            f"origen={self.origen} tenant={self.tenant_id}>"
        )


class EntradaPadron(TenantScopedMixin, Base):
    """Entrada individual del padrón: un alumno en una version de padrón.

    email se almacena cifrado AES-256-GCM.
    usuario_id es nullable (alumno sin cuenta en el sistema).
    """

    __tablename__ = "entrada_padron"

    version_padron_id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("version_padron.id", ondelete="CASCADE"),
        nullable=False,
        comment="UUID de la versión de padrón a la que pertenece",
    )
    nombre: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Nombre del alumno",
    )
    apellidos: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Apellidos del alumno",
    )
    email_encrypted: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Email cifrado AES-256-GCM (ciphertext en base64)",
    )
    comision: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Comisión del alumno",
    )
    regional: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Regional / sede del alumno (opcional)",
    )
    usuario_id: Mapped[_uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="SET NULL"),
        nullable=True,
        comment="UUID del usuario si el alumno ya tiene cuenta en el sistema",
    )

    @declared_attr
    def __table_args__(cls) -> tuple:
        return (
            Index(
                f"ix_{cls.__tablename__}_tenant_version",
                "tenant_id",
                "version_padron_id",
            ),
            Index(
                f"ix_{cls.__tablename__}_tenant_deleted",
                "tenant_id",
                "deleted_at",
            ),
        )

    def __repr__(self) -> str:
        # NUNCA incluir email en texto plano en repr/logs
        return (
            f"<EntradaPadron id={self.id} nombre={self.nombre} "
            f"apellidos={self.apellidos} version={self.version_padron_id}>"
        )

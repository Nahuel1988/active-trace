"""Modelos Permiso y RolPermiso — catálogo de permisos y matriz rol × permiso.

Permiso: capacidad atómica expresada como ``modulo:accion``, tenant-scoped.
RolPermiso: asociación rol ↔ permiso con scope (global | propio).
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    CheckConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, declared_attr, mapped_column

from app.core.database import Base
from app.models.base import TenantScopedMixin


class Permiso(TenantScopedMixin, Base):
    """Capacidad atómica ``modulo:accion``, tenant-scoped, soft-delete.

    Attributes:
        modulo: Módulo funcional (ej: ``comunicacion``, ``calificaciones``).
        accion: Acción dentro del módulo (ej: ``aprobar``, ``importar``).
        code: Clave derivada ``"{modulo}:{accion}"``, única por tenant.
    """

    __tablename__ = "permiso"

    modulo: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Módulo funcional (ej: comunicacion, calificaciones)",
    )
    accion: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Acción dentro del módulo (ej: aprobar, importar)",
    )
    code: Mapped[str] = mapped_column(
        String(201),
        nullable=False,
        comment="Clave única derivada '{modulo}:{accion}'",
    )

    @declared_attr
    def __table_args__(cls) -> tuple:
        return (
            UniqueConstraint(
                "tenant_id",
                "code",
                name=f"uq_{cls.__tablename__}_tenant_code",
            ),
            Index(
                f"ix_{cls.__tablename__}_tenant_deleted",
                "tenant_id",
                "deleted_at",
            ),
            CheckConstraint(
                "code ~ '^[a-z_]+:[a-z_]+$'",
                name=f"ck_{cls.__tablename__}_code_format",
            ),
        )

    def __repr__(self) -> str:
        return f"<Permiso id={self.id} code='{self.code}'>"


class RolPermiso(Base):
    """Matriz rol × permiso con scope.

    PK compuesta: ``(tenant_id, role_id, permiso_id)``.

    Attributes:
        scope: Alcance del permiso para este rol:
            ``global`` — aplica a cualquier recurso;
            ``propio`` — solo sobre recursos propios del usuario.
    """

    __tablename__ = "rol_permiso"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenant.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("role.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    permiso_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("permiso.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    scope: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="Alcance: 'global' (cualquier recurso) o 'propio' (solo propio)",
    )
    asignado_por: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="SET NULL"),
        nullable=True,
        comment="UUID del usuario que asignó este permiso al rol (auditoría)",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    @declared_attr
    def __table_args__(cls) -> tuple:
        return (
            CheckConstraint(
                "scope IN ('global', 'propio')",
                name=f"ck_{cls.__tablename__}_scope",
            ),
            Index(
                f"ix_{cls.__tablename__}_tenant_role",
                "tenant_id",
                "role_id",
            ),
            Index(
                f"ix_{cls.__tablename__}_tenant_permiso",
                "tenant_id",
                "permiso_id",
            ),
        )

    def __repr__(self) -> str:
        return (
            f"<RolPermiso role={self.role_id} permiso={self.permiso_id} "
            f"scope='{self.scope}'>"
        )

"""Modelos Role y UserRole — RBAC multi-tenant.

Role: catálogo de roles disponibles por tenant.
UserRole: asignación de roles a usuarios con vigencia (desde/hasta).
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, declared_attr, mapped_column

from app.core.database import Base
from app.models.base import TenantScopedMixin


class Role(TenantScopedMixin, Base):
    __tablename__ = "role"

    code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Código interno del rol (ej: admin, profesor, alumno)",
    )
    nombre: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Nombre legible del rol (ej: Administrador, Profesor)",
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
        )

    def __repr__(self) -> str:
        return f"<Role id={self.id} code='{self.code}'>"


class UserRole(Base):
    """Asociación usuario-rol con vigencia.

    PK compuesta: (user_id, role_id, tenant_id, desde).
    Permite múltiples asignaciones del mismo rol al mismo usuario
    en distintos períodos (re-asignación histórica).
    """

    __tablename__ = "user_role"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("role.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenant.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    desde: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        primary_key=True,
        server_default=func.now(),
        nullable=False,
    )
    hasta: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="NULL = vigente; con fecha = desactivado desde ese momento",
    )

    def __repr__(self) -> str:
        return f"<UserRole user={self.user_id} role={self.role_id} desde={self.desde}>"

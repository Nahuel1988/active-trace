"""Mixins base para modelos del dominio.

TenantScopedMixin — aplica UUID PK, tenant_id FK, timestamps y soft delete
a todo modelo de dominio que lo herede.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, declared_attr, mapped_column


class TenantScopedMixin:
    """Mixin que agrega columnas tenant-aware a cualquier modelo SQLAlchemy.

    Columnas:
        id: UUID v4, PK, generado en Python.
        tenant_id: UUID, FK → tenant.id, NOT NULL, indexado.
        created_at: datetime UTC, auto-set en INSERT.
        updated_at: datetime UTC, auto-set en INSERT y UPDATE.
        deleted_at: datetime UTC nullable; NULL = activo (soft delete).
    """

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
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    @declared_attr
    def __table_args__(cls) -> tuple:  # noqa: N805
        return (
            Index(
                f"ix_{cls.__tablename__}_tenant_deleted",
                "tenant_id",
                "deleted_at",
            ),
        )

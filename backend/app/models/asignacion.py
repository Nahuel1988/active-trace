"""Modelo Asignacion — vinculación usuario × rol × contexto académico.

Convive con UserRole (C-03): UserRole cubre roles globales del tenant
(ADMIN, FINANZAS); Asignacion cubre roles con contexto académico
(PROFESOR, TUTOR, COORDINADOR, NEXO) con jerarquía y vigencia.

Decisiones de diseño (aprobadas en CHECKPOINT C-07):
- D1: FKs nullable a materia, carrera, cohorte, responsable (combinación válida
      se valida en AsignacionService según la tabla de roles).
- D3: Tabla única, no una por contexto.
- D4: estado_vigencia es @property derivado, no columna persistida.
- D7: Soft delete (deleted_at). Vencida != soft-deleted.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, declared_attr, mapped_column
from sqlalchemy import String

from app.core.database import Base
from app.models.base import TenantScopedMixin


# Roles permitidos en Asignacion (ADMIN y FINANZAS van en UserRole)
ROLES_EN_ASIGNACION = frozenset({
    "PROFESOR",
    "TUTOR",
    "COORDINADOR",
    "NEXO",
})

ESTADO_VIGENTE = "Vigente"
ESTADO_VENCIDA = "Vencida"


class Asignacion(TenantScopedMixin, Base):
    """Asignación de un usuario a un rol con contexto académico y vigencia.

    Attributes:
        usuario_id: UUID del usuario asignado (FK → user.id, NOT NULL).
        role_id: UUID del rol (FK → role.id, NOT NULL).
        materia_id: UUID de la materia (nullable; requerido para PROFESOR/TUTOR).
        carrera_id: UUID de la carrera (nullable; requerido para PROFESOR/TUTOR/COORDINADOR).
        cohorte_id: UUID de la cohorte (nullable; requerido para PROFESOR/TUTOR).
        responsable_id: UUID del responsable jerárquico (nullable).
        comisiones: Array de strings con identificadores de comisión.
        desde: Fecha de inicio de vigencia (NOT NULL).
        hasta: Fecha de fin de vigencia (NULL = indefinida).
        estado_vigencia: Propiedad derivada 'Vigente' | 'Vencida'.
    """

    __tablename__ = "asignacion"

    # -----------------------------------------------------------------------
    # FKs obligatorias
    # -----------------------------------------------------------------------
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        comment="Usuario asignado",
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("role.id", ondelete="CASCADE"),
        nullable=False,
        comment="Rol asignado (PROFESOR, TUTOR, COORDINADOR o NEXO)",
    )

    # -----------------------------------------------------------------------
    # FKs de contexto académico — nullable
    # -----------------------------------------------------------------------
    materia_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("materia.id", ondelete="SET NULL"),
        nullable=True,
        comment="Materia (requerida para PROFESOR/TUTOR; NULL para COORDINADOR/NEXO)",
    )
    carrera_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("carrera.id", ondelete="SET NULL"),
        nullable=True,
        comment="Carrera (requerida para PROFESOR/TUTOR/COORDINADOR; NULL para NEXO)",
    )
    cohorte_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cohorte.id", ondelete="SET NULL"),
        nullable=True,
        comment="Cohorte (requerida para PROFESOR/TUTOR; NULL para COORDINADOR/NEXO)",
    )
    responsable_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="SET NULL"),
        nullable=True,
        comment="Responsable jerárquico (nullable; valida ciclos en service)",
    )

    # -----------------------------------------------------------------------
    # Comisiones — ARRAY de strings
    # -----------------------------------------------------------------------
    comisiones: Mapped[list[str] | None] = mapped_column(
        ARRAY(String),
        nullable=True,
        default=list,
        server_default="{}",
        comment="Comisiones de la asignación (puede ser vacío)",
    )

    # -----------------------------------------------------------------------
    # Vigencia
    # -----------------------------------------------------------------------
    desde: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="Inicio de vigencia de la asignación",
    )
    hasta: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Fin de vigencia (NULL = indefinida)",
    )

    @declared_attr
    def __table_args__(cls) -> tuple:  # noqa: N805
        return (
            Index(
                "ix_asignacion_tenant_usuario",
                "tenant_id",
                "usuario_id",
            ),
            Index(
                "ix_asignacion_tenant_responsable",
                "tenant_id",
                "responsable_id",
            ),
            Index(
                "ix_asignacion_tenant_deleted",
                "tenant_id",
                "deleted_at",
            ),
        )

    @hybrid_property
    def estado_vigencia(self) -> str:
        """Propiedad derivada de vigencia temporal (no persistida).

        Returns:
            'Vigente' si desde <= now AND (hasta IS NULL OR hasta >= now).
            'Vencida' en cualquier otro caso (vencida o no comenzada).
        """
        now = datetime.now(timezone.utc)
        # Asegurar que las fechas del modelo sean timezone-aware para comparación
        desde = self.desde
        if desde is None:
            return ESTADO_VENCIDA
        # Normalizar a UTC si no tiene tz
        if desde.tzinfo is None:
            desde = desde.replace(tzinfo=timezone.utc)
        if desde > now:
            return ESTADO_VENCIDA
        hasta = self.hasta
        if hasta is None:
            return ESTADO_VIGENTE
        if hasta.tzinfo is None:
            hasta = hasta.replace(tzinfo=timezone.utc)
        return ESTADO_VIGENTE if hasta >= now else ESTADO_VENCIDA

    def __repr__(self) -> str:
        return (
            f"<Asignacion id={self.id} tenant={self.tenant_id} "
            f"usuario={self.usuario_id} role={self.role_id} "
            f"desde={self.desde} hasta={self.hasta}>"
        )

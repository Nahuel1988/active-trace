"""009_calificacion_umbral_materia

C-10: Crea las tablas ``calificacion`` y ``umbral_materia`` con FKs
a ``entrada_padron``, ``materia``, ``user``, ``asignacion``. Incluye
índices compuestos y UniqueConstraint scoped al tenant.

Merge migration: depende de los tres heads 008_encuentros_y_guardias,
008_evaluaciones y 008_version_padron_entrada_padron, que son hermanos
con padre común 007_tareas_internas.

Revision ID: 009_calificacion_umbral_materia
Revises: 008_encuentros_y_guardias, 008_evaluaciones, 008_version_padron_entrada_padron
Create Date: 2026-06-19 20:30:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "009_calificacion_umbral_materia"
down_revision = (
    "008_encuentros_y_guardias",
    "008_evaluaciones",
    "008_version_padron_entrada_padron",
)
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # Tabla: calificacion
    # ------------------------------------------------------------------
    op.create_table(
        "calificacion",
        # TenantScopedMixin
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        # Columnas de dominio
        sa.Column("entrada_padron_id", postgresql.UUID(as_uuid=True), nullable=False,
                  comment="FK → EntradaPadron (alumno)"),
        sa.Column("materia_id", postgresql.UUID(as_uuid=True), nullable=False,
                  comment="FK → Materia"),
        sa.Column("actividad", sa.String(length=255), nullable=False,
                  comment="Nombre de la actividad (ej: TP1, Examen Parcial)"),
        sa.Column("nota_numerica", sa.Float(), nullable=True,
                  comment="Nota numérica (nullable — puede ser solo textual)"),
        sa.Column("nota_textual", sa.String(length=255), nullable=True,
                  comment="Nota textual (nullable — puede ser solo numérica)"),
        sa.Column("origen", sa.Enum(
            "importado", "manual", name="origen_calificacion",
            create_constraint=True),
            nullable=False, server_default=sa.text("'importado'"),
            comment="Origen: importado (archivo) o manual"),
        sa.Column("creado_por", postgresql.UUID(as_uuid=True), nullable=False,
                  comment="FK → User que importó/creó la calificación"),
        sa.Column("deleted_by", postgresql.UUID(as_uuid=True), nullable=True,
                  comment="UUID del usuario que realizó el soft-delete (vaciado)"),
        # FKs
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["entrada_padron_id"], ["entrada_padron.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["materia_id"], ["materia.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["creado_por"], ["user.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Índices compuestos
    op.create_index(
        "ix_calificacion_tenant_materia_creador",
        "calificacion",
        ["tenant_id", "materia_id", "creado_por"],
        unique=False,
    )
    op.create_index(
        "ix_calificacion_tenant_entrada",
        "calificacion",
        ["tenant_id", "entrada_padron_id"],
        unique=False,
    )
    op.create_index(
        "ix_calificacion_tenant_deleted",
        "calificacion",
        ["tenant_id", "deleted_at"],
        unique=False,
    )

    # ------------------------------------------------------------------
    # Tabla: umbral_materia
    # ------------------------------------------------------------------
    op.create_table(
        "umbral_materia",
        # TenantScopedMixin
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        # Columnas de dominio
        sa.Column("asignacion_id", postgresql.UUID(as_uuid=True), nullable=False,
                  comment="FK → Asignacion (docente × materia)"),
        sa.Column("materia_id", postgresql.UUID(as_uuid=True), nullable=False,
                  comment="FK → Materia"),
        sa.Column("umbral_pct", sa.Integer(), nullable=False,
                  server_default=sa.text("60"),
                  comment="Porcentaje mínimo para aprobar (default 60)"),
        sa.Column("valores_aprobatorios", postgresql.JSONB(), nullable=True,
                  comment="Lista de valores textuales que cuentan como aprobado"),
        # FKs
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["asignacion_id"], ["asignacion.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["materia_id"], ["materia.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        # UniqueConstraint scoped al tenant
        sa.UniqueConstraint(
            "tenant_id", "asignacion_id", "materia_id",
            name="uq_umbral_materia_tenant_asignacion_materia",
        ),
    )

    # Índices
    op.create_index(
        "ix_umbral_materia_tenant_asignacion",
        "umbral_materia",
        ["tenant_id", "asignacion_id"],
        unique=False,
    )
    op.create_index(
        "ix_umbral_materia_tenant_deleted",
        "umbral_materia",
        ["tenant_id", "deleted_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_table("umbral_materia")
    op.drop_table("calificacion")
    # Limpiar el enum creado por SQLAlchemy
    op.execute("DROP TYPE IF EXISTS origen_calificacion")

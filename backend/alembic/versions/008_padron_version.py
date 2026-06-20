"""008_padron_version

C-09: Crea las tablas ``version_padron`` y ``entrada_padron`` con FKs
a ``materia``, ``cohorte`` y ``user``. Incluye el índice parcial
UNIQUE para la invariante de una sola versión activa por tupla
(tenant, materia, cohorte).

Revision ID: 008_padron_version
Revises: 007_tareas_internas
Create Date: 2026-06-19 20:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "008_padron_version"
down_revision = "007_tareas_internas"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # Tabla: version_padron
    # ------------------------------------------------------------------
    op.create_table(
        "version_padron",
        # TenantScopedMixin
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        # Columnas de dominio
        sa.Column("materia_id", postgresql.UUID(as_uuid=True), nullable=False,
                  comment="UUID de la materia"),
        sa.Column("cohorte_id", postgresql.UUID(as_uuid=True), nullable=False,
                  comment="UUID de la cohorte"),
        sa.Column("activa", sa.Boolean(), nullable=False,
                  server_default=sa.text("true"),
                  comment="True si es la versión activa para la tupla"),
        sa.Column("total_entradas", sa.Integer(), nullable=False,
                  server_default=sa.text("0"),
                  comment="Cantidad de entradas en esta versión"),
        sa.Column("origen", sa.String(length=20), nullable=False,
                  comment="Origen: 'archivo' | 'moodle' | 'manual'"),
        # FKs
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["materia_id"], ["materia.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["cohorte_id"], ["cohorte.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Invariante D-01: una sola versión activa por (tenant, materia, cohorte)
    op.create_index(
        "uq_version_padron_activa_por_tupla",
        "version_padron",
        ["tenant_id", "materia_id", "cohorte_id"],
        unique=True,
        postgresql_where=sa.text("activa = true"),
    )

    op.create_index(
        "ix_version_padron_tenant_materia_cohorte",
        "version_padron",
        ["tenant_id", "materia_id", "cohorte_id"],
        unique=False,
    )
    op.create_index(
        "ix_version_padron_tenant_deleted",
        "version_padron",
        ["tenant_id", "deleted_at"],
        unique=False,
    )

    # ------------------------------------------------------------------
    # Tabla: entrada_padron
    # ------------------------------------------------------------------
    op.create_table(
        "entrada_padron",
        # TenantScopedMixin
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        # Columnas de dominio
        sa.Column("version_padron_id", postgresql.UUID(as_uuid=True), nullable=False,
                  comment="UUID de la versión de padrón"),
        sa.Column("nombre", sa.String(length=255), nullable=False,
                  comment="Nombre del alumno"),
        sa.Column("apellidos", sa.String(length=255), nullable=False,
                  comment="Apellidos del alumno"),
        sa.Column("email_encrypted", sa.Text(), nullable=False,
                  comment="Email cifrado AES-256-GCM"),
        sa.Column("comision", sa.String(length=100), nullable=False,
                  comment="Comisión del alumno"),
        sa.Column("regional", sa.String(length=255), nullable=True,
                  comment="Regional / sede del alumno"),
        sa.Column("usuario_id", postgresql.UUID(as_uuid=True), nullable=True,
                  comment="UUID del usuario si tiene cuenta en el sistema"),
        # FKs
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["version_padron_id"], ["version_padron.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["usuario_id"], ["user.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_entrada_padron_tenant_version",
        "entrada_padron",
        ["tenant_id", "version_padron_id"],
        unique=False,
    )
    op.create_index(
        "ix_entrada_padron_tenant_deleted",
        "entrada_padron",
        ["tenant_id", "deleted_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_table("entrada_padron")
    op.drop_table("version_padron")

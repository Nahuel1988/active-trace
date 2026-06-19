"""007_tareas_internas

C-16: Crea las tablas ``tarea`` y ``comentario_tarea`` con FKs a
``user``, ``materia`` y los índices de filtro requeridos (D-05).

Merge migration: depende de ambos heads 006_usuarios_y_asignaciones
y 601bb609ae5b (006_programas_y_fechas_academicas), que son hermanos
con padre común 005_estructura_academica.

Revision ID: 007_tareas_internas
Revises: 006_usuarios_y_asignaciones, 601bb609ae5b
Create Date: 2026-06-19 19:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "007_tareas_internas"
down_revision = ("006_usuarios_y_asignaciones", "601bb609ae5b")
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # Tabla: tarea
    # ------------------------------------------------------------------
    op.create_table(
        "tarea",
        # TenantScopedMixin
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        # Columnas de dominio
        sa.Column("descripcion", sa.Text(), nullable=False,
                  comment="Descripción de la tarea"),
        sa.Column("estado", sa.String(length=32), nullable=False,
                  server_default=sa.text("'Pendiente'"),
                  comment="Estado: Pendiente/EnProgreso/Resuelta/Cancelada"),
        sa.Column("asignado_a", postgresql.UUID(as_uuid=True), nullable=False,
                  comment="UUID del usuario asignado a resolver"),
        sa.Column("asignado_por", postgresql.UUID(as_uuid=True), nullable=False,
                  comment="UUID del usuario que asignó/delegó"),
        sa.Column("materia_id", postgresql.UUID(as_uuid=True), nullable=True,
                  comment="UUID de la materia asociada (opcional)"),
        sa.Column("contexto_id", postgresql.UUID(as_uuid=True), nullable=True,
                  comment="UUID ref. genérica a otra entidad (sin FK)"),
        # FKs
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["asignado_a"], ["user.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["asignado_por"], ["user.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["materia_id"], ["materia.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Índices de filtro sobre tarea (D-05)
    op.create_index("ix_tarea_tenant_asignado_a", "tarea",
                    ["tenant_id", "asignado_a"], unique=False)
    op.create_index("ix_tarea_tenant_asignado_por", "tarea",
                    ["tenant_id", "asignado_por"], unique=False)
    op.create_index("ix_tarea_tenant_materia_id", "tarea",
                    ["tenant_id", "materia_id"], unique=False)
    op.create_index("ix_tarea_tenant_estado", "tarea",
                    ["tenant_id", "estado"], unique=False)
    op.create_index("ix_tarea_tenant_deleted", "tarea",
                    ["tenant_id", "deleted_at"], unique=False)

    # ------------------------------------------------------------------
    # Tabla: comentario_tarea (append-only, sin updated_at / deleted_at)
    # ------------------------------------------------------------------
    op.create_table(
        "comentario_tarea",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tarea_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("autor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("texto", sa.Text(), nullable=False,
                  comment="Contenido del comentario"),
        sa.Column("creado_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        # FKs
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tarea_id"], ["tarea.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["autor_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("ix_comentario_tarea_tenant_tarea", "comentario_tarea",
                    ["tenant_id", "tarea_id"], unique=False)


def downgrade() -> None:
    op.drop_table("comentario_tarea")
    op.drop_table("tarea")

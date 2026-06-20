"""008_encuentros_y_guardias

C-13: Crea tablas slot_encuentro, instancia_encuentro y guardia con
enums, FKs a asignacion/materia/carrera/cohorte, e índices compuestos
de filtro multi-tenant.

Merge migration: depende de los tres heads actuales (006_avisos,
007_perfil_y_mensajeria, 007_tareas_internas) para unificar la línea.

Revision ID: 008_encuentros_y_guardias
Revises: 006_avisos, 007_perfil_y_mensajeria, 007_tareas_internas
Create Date: 2026-06-19 20:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "008_encuentros_y_guardias"
down_revision = ("006_avisos", "007_perfil_y_mensajeria", "007_tareas_internas")
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -----------------------------------------------------------------------
    # 1. Enums
    # -----------------------------------------------------------------------
    op.execute("CREATE TYPE diasemana AS ENUM ('lunes','martes','miercoles','jueves','viernes','sabado','domingo')")
    op.execute("CREATE TYPE estadoinstancia AS ENUM ('programado','realizado','cancelado')")
    op.execute("CREATE TYPE estadoguardia AS ENUM ('pendiente','realizada','cancelada')")

    # -----------------------------------------------------------------------
    # 2. Tabla slot_encuentro
    # -----------------------------------------------------------------------
    op.create_table(
        "slot_encuentro",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True, default=None),
        sa.Column("asignacion_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("asignacion.id", ondelete="CASCADE"), nullable=False),
        sa.Column("materia_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("materia.id", ondelete="CASCADE"), nullable=False),
        sa.Column("titulo", sa.Text, nullable=False),
        sa.Column("hora", sa.Time, nullable=False),
        sa.Column("dia_semana", sa.Enum("lunes", "martes", "miercoles", "jueves",
                  "viernes", "sabado", "domingo", name="diasemana"), nullable=False),
        sa.Column("fecha_inicio", sa.Date, nullable=False),
        sa.Column("cant_semanas", sa.Integer, nullable=False, server_default="0"),
        sa.Column("fecha_unica", sa.Date, nullable=True, default=None),
        sa.Column("meet_url", sa.Text, nullable=True, default=None),
        sa.Column("vig_desde", sa.Date, nullable=False),
        sa.Column("vig_hasta", sa.Date, nullable=True, default=None),
    )
    op.create_index(
        "ix_slot_encuentro_tenant_materia",
        "slot_encuentro", ["tenant_id", "materia_id"],
    )
    op.create_index(
        "ix_slot_encuentro_tenant_asignacion",
        "slot_encuentro", ["tenant_id", "asignacion_id"],
    )
    op.create_index(
        "ix_slot_encuentro_tenant_deleted",
        "slot_encuentro", ["tenant_id", "deleted_at"],
    )

    # -----------------------------------------------------------------------
    # 3. Tabla instancia_encuentro
    # -----------------------------------------------------------------------
    op.create_table(
        "instancia_encuentro",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True, default=None),
        sa.Column("slot_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("slot_encuentro.id", ondelete="SET NULL"),
                  nullable=True, default=None),
        sa.Column("materia_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("materia.id", ondelete="CASCADE"), nullable=False),
        sa.Column("fecha", sa.Date, nullable=False),
        sa.Column("hora", sa.Time, nullable=False),
        sa.Column("titulo", sa.Text, nullable=False),
        sa.Column("estado", sa.Enum("programado", "realizado", "cancelado",
                  name="estadoinstancia"), nullable=False, server_default="programado"),
        sa.Column("meet_url", sa.Text, nullable=True, default=None),
        sa.Column("video_url", sa.Text, nullable=True, default=None),
        sa.Column("comentario", sa.Text, nullable=True, default=None),
    )
    op.create_index(
        "ix_instancia_encuentro_tenant_slot",
        "instancia_encuentro", ["tenant_id", "slot_id"],
    )
    op.create_index(
        "ix_instancia_encuentro_tenant_materia",
        "instancia_encuentro", ["tenant_id", "materia_id"],
    )
    op.create_index(
        "ix_instancia_encuentro_tenant_estado",
        "instancia_encuentro", ["tenant_id", "estado"],
    )
    op.create_index(
        "ix_instancia_encuentro_tenant_fecha",
        "instancia_encuentro", ["tenant_id", "fecha"],
    )
    op.create_index(
        "ix_instancia_encuentro_tenant_deleted",
        "instancia_encuentro", ["tenant_id", "deleted_at"],
    )

    # -----------------------------------------------------------------------
    # 4. Tabla guardia
    # -----------------------------------------------------------------------
    op.create_table(
        "guardia",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True, default=None),
        sa.Column("asignacion_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("asignacion.id", ondelete="CASCADE"), nullable=False),
        sa.Column("materia_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("materia.id", ondelete="CASCADE"), nullable=False),
        sa.Column("carrera_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("carrera.id", ondelete="CASCADE"), nullable=False),
        sa.Column("cohorte_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("cohorte.id", ondelete="CASCADE"), nullable=False),
        sa.Column("dia", sa.Enum("lunes", "martes", "miercoles", "jueves",
                  "viernes", "sabado", "domingo", name="diasemana"), nullable=False),
        sa.Column("horario", sa.Text, nullable=False),
        sa.Column("estado", sa.Enum("pendiente", "realizada", "cancelada",
                  name="estadoguardia"), nullable=False, server_default="pendiente"),
        sa.Column("comentarios", sa.Text, nullable=True, default=None),
        sa.Column("creada_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ix_guardia_tenant_asignacion",
        "guardia", ["tenant_id", "asignacion_id"],
    )
    op.create_index(
        "ix_guardia_tenant_materia",
        "guardia", ["tenant_id", "materia_id"],
    )
    op.create_index(
        "ix_guardia_tenant_estado",
        "guardia", ["tenant_id", "estado"],
    )
    op.create_index(
        "ix_guardia_tenant_deleted",
        "guardia", ["tenant_id", "deleted_at"],
    )


def downgrade() -> None:
    # Orden inverso de FK
    op.drop_table("guardia")
    op.drop_table("instancia_encuentro")
    op.drop_table("slot_encuentro")
    op.execute("DROP TYPE IF EXISTS estadoguardia")
    op.execute("DROP TYPE IF EXISTS estadoinstancia")
    op.execute("DROP TYPE IF EXISTS diasemana")

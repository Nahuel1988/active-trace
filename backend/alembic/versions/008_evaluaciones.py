"""008_evaluaciones

C-14: Crea las tablas ``evaluacion``, ``reserva_evaluacion`` y
``resultado_evaluacion`` con FKs a materia, cohorte y user,
incluyendo constraints de unicidad compuesta.

Revision ID: 008_evaluaciones
Revises: 007_tareas_internas, 007_perfil_y_mensajeria
Create Date: 2026-06-19 00:00:00.000000
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "008_evaluaciones"
down_revision = ("007_tareas_internas", "007_perfil_y_mensajeria")
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # evaluacion
    # ------------------------------------------------------------------
    op.create_table(
        "evaluacion",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("materia_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("cohorte_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tipo", sa.String(length=32), nullable=False),
        sa.Column("instancia", sa.String(length=255), nullable=False),
        sa.Column("dias_disponibles", sa.Integer(), nullable=False),
        sa.Column("candidatos", postgresql.JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["materia_id"], ["materia.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["cohorte_id"], ["cohorte.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_evaluacion_tenant_deleted", "evaluacion", ["tenant_id", "deleted_at"], unique=False)
    op.create_index("ix_evaluacion_tenant_id", "evaluacion", ["tenant_id"], unique=False)
    op.create_index("ix_evaluacion_materia_id", "evaluacion", ["materia_id"], unique=False)
    op.create_index("ix_evaluacion_cohorte_id", "evaluacion", ["cohorte_id"], unique=False)

    # ------------------------------------------------------------------
    # reserva_evaluacion
    # ------------------------------------------------------------------
    op.create_table(
        "reserva_evaluacion",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("evaluacion_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("alumno_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("fecha_hora", sa.DateTime(timezone=True), nullable=False),
        sa.Column("estado", sa.String(length=16), nullable=False, server_default=sa.text("'Activa'")),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["evaluacion_id"], ["evaluacion.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["alumno_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_reserva_evaluacion_tenant_deleted", "reserva_evaluacion", ["tenant_id", "deleted_at"], unique=False)
    op.create_index("ix_reserva_evaluacion_tenant_id", "reserva_evaluacion", ["tenant_id"], unique=False)
    op.create_index("ix_reserva_evaluacion_evaluacion_id", "reserva_evaluacion", ["evaluacion_id"], unique=False)
    op.create_index("ix_reserva_evaluacion_alumno_id", "reserva_evaluacion", ["alumno_id"], unique=False)
    op.create_index("ix_reserva_evaluacion_estado", "reserva_evaluacion", ["estado"], unique=False)
    op.create_index(
        "uq_reserva_evaluacion_tenant_evaluacion_alumno_activa",
        "reserva_evaluacion",
        ["tenant_id", "evaluacion_id", "alumno_id"],
        unique=True,
        postgresql_where=sa.text("estado = 'Activa'"),
    )

    # ------------------------------------------------------------------
    # resultado_evaluacion
    # ------------------------------------------------------------------
    op.create_table(
        "resultado_evaluacion",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("evaluacion_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("alumno_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("nota_final", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["evaluacion_id"], ["evaluacion.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["alumno_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_resultado_evaluacion_tenant_deleted", "resultado_evaluacion", ["tenant_id", "deleted_at"], unique=False)
    op.create_index("ix_resultado_evaluacion_tenant_id", "resultado_evaluacion", ["tenant_id"], unique=False)
    op.create_index("ix_resultado_evaluacion_evaluacion_id", "resultado_evaluacion", ["evaluacion_id"], unique=False)
    op.create_index("ix_resultado_evaluacion_alumno_id", "resultado_evaluacion", ["alumno_id"], unique=False)
    op.create_unique_constraint(
        "uq_resultado_evaluacion_tenant_evaluacion_alumno",
        "resultado_evaluacion",
        ["tenant_id", "evaluacion_id", "alumno_id"],
    )


def downgrade() -> None:
    op.drop_table("resultado_evaluacion")
    op.drop_table("reserva_evaluacion")
    op.drop_table("evaluacion")

"""006_programas_y_fechas_academicas

Revision ID: 601bb609ae5b
Revises: 005_estructura_academica
Create Date: 2026-06-19 18:12:30.715405
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = '601bb609ae5b'
down_revision: Union[str, None] = '005_estructura_academica'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # programa_materia
    op.create_table(
        "programa_materia",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("materia_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("carrera_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("cohorte_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("titulo", sa.String(length=255), nullable=False),
        sa.Column("referencia_archivo", sa.String(length=1024), nullable=True),
        sa.Column("cargado_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["materia_id"], ["materia.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["carrera_id"], ["carrera.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["cohorte_id"], ["cohorte.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_programa_materia_tenant_deleted", "programa_materia", ["tenant_id", "deleted_at"], unique=False)
    op.create_index("ix_programa_materia_tenant_id", "programa_materia", ["tenant_id"], unique=False)
    op.create_unique_constraint(
        "uq_programa_materia_combinacion", "programa_materia",
        ["tenant_id", "materia_id", "carrera_id", "cohorte_id"],
    )

    # fecha_academica
    op.create_table(
        "fecha_academica",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("materia_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("cohorte_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tipo", sa.String(length=32), nullable=False),
        sa.Column("numero", sa.Integer(), nullable=False),
        sa.Column("periodo", sa.String(length=64), nullable=False),
        sa.Column("fecha", sa.DateTime(timezone=True), nullable=False),
        sa.Column("titulo", sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["materia_id"], ["materia.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["cohorte_id"], ["cohorte.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_fecha_academica_tenant_deleted", "fecha_academica", ["tenant_id", "deleted_at"], unique=False)
    op.create_index("ix_fecha_academica_tenant_id", "fecha_academica", ["tenant_id"], unique=False)
    op.create_index("ix_fecha_academica_cohorte_id", "fecha_academica", ["tenant_id", "cohorte_id"], unique=False)
    op.create_unique_constraint(
        "uq_fecha_academica_combinacion", "fecha_academica",
        ["tenant_id", "materia_id", "cohorte_id", "tipo", "numero"],
    )


def downgrade() -> None:
    op.drop_table("fecha_academica")
    op.drop_table("programa_materia")

"""005_estructura_academica

Revision ID: 005_estructura_academica
Revises: 03dd2a3696a9
Create Date: 2026-06-19 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "005_estructura_academica"
down_revision = "03dd2a3696a9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # carrera
    op.create_table(
        "carrera",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("codigo", sa.String(length=64), nullable=False),
        sa.Column("nombre", sa.String(length=255), nullable=False),
        sa.Column("estado", sa.String(length=32), nullable=False, server_default=sa.text("'activa'")),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_carrera_tenant_deleted", "carrera", ["tenant_id", "deleted_at"], unique=False)
    op.create_index("ix_carrera_tenant_id", "carrera", ["tenant_id"], unique=False)
    op.create_unique_constraint("uq_carrera_tenant_codigo", "carrera", ["tenant_id", "codigo"])

    # cohorte
    op.create_table(
        "cohorte",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("carrera_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("nombre", sa.String(length=128), nullable=False),
        sa.Column("anio", sa.Integer(), nullable=False),
        sa.Column("vig_desde", sa.String(length=20), nullable=False),
        sa.Column("vig_hasta", sa.String(length=20), nullable=True),
        sa.Column("estado", sa.String(length=16), nullable=False, server_default=sa.text("'activa'")),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["carrera_id"], ["carrera.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_cohorte_tenant_deleted", "cohorte", ["tenant_id", "deleted_at"], unique=False)
    op.create_index("ix_cohorte_tenant_id", "cohorte", ["tenant_id"], unique=False)
    op.create_unique_constraint("uq_cohorte_tenant_carrera_nombre", "cohorte", ["tenant_id", "carrera_id", "nombre"])

    # materia
    op.create_table(
        "materia",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("codigo", sa.String(length=64), nullable=False),
        sa.Column("nombre", sa.String(length=255), nullable=False),
        sa.Column("estado", sa.String(length=16), nullable=False, server_default=sa.text("'activa'")),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_materia_tenant_deleted", "materia", ["tenant_id", "deleted_at"], unique=False)
    op.create_index("ix_materia_tenant_id", "materia", ["tenant_id"], unique=False)
    op.create_unique_constraint("uq_materia_tenant_codigo", "materia", ["tenant_id", "codigo"])


def downgrade() -> None:
    op.drop_table("materia")
    op.drop_table("cohorte")
    op.drop_table("carrera")

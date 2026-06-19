"""006_avisos

Revision ID: 006_avisos
Revises: 005_estructura_academica
Create Date: 2026-06-19 17:50:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "006_avisos"
down_revision: Union[str, None] = "005_estructura_academica"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -----------------------------------------------------------------------
    # 1. Tipo enum alcance_aviso
    # -----------------------------------------------------------------------
    op.execute("CREATE TYPE alcance_aviso AS ENUM ('global', 'por_materia', 'por_cohorte', 'por_rol')")

    # -----------------------------------------------------------------------
    # 2. Tipo enum severidad_aviso
    # -----------------------------------------------------------------------
    op.execute("CREATE TYPE severidad_aviso AS ENUM ('info', 'advertencia', 'critico')")

    # -----------------------------------------------------------------------
    # 3. Tabla aviso
    # -----------------------------------------------------------------------
    op.create_table(
        "aviso",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),

        sa.Column("alcance", postgresql.ENUM("global", "por_materia", "por_cohorte", "por_rol", name="alcance_aviso", create_type=False), nullable=False),
        sa.Column("materia_id", sa.UUID(), nullable=True),
        sa.Column("cohorte_id", sa.UUID(), nullable=True),
        sa.Column("rol_destino", sa.String(32), nullable=True),
        sa.Column("severidad", postgresql.ENUM("info", "advertencia", "critico", name="severidad_aviso", create_type=False), nullable=False),
        sa.Column("titulo", sa.String(255), nullable=False),
        sa.Column("cuerpo", sa.Text(), nullable=False),
        sa.Column("inicio_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fin_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("orden", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("requiere_ack", sa.Boolean(), nullable=False, server_default=sa.text("false")),

        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["materia_id"], ["materia.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["cohorte_id"], ["cohorte.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_aviso_tenant_deleted", "aviso", ["tenant_id", "deleted_at"], unique=False)
    op.create_index(op.f("ix_aviso_tenant_id"), "aviso", ["tenant_id"], unique=False)
    op.create_index(
        "ix_aviso_tenant_activo_vigencia",
        "aviso",
        ["tenant_id", "activo", "inicio_en", "fin_en"],
        unique=False,
    )

    # -----------------------------------------------------------------------
    # 4. Tabla acknowledgment_aviso (append-only)
    # -----------------------------------------------------------------------
    op.create_table(
        "acknowledgment_aviso",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("aviso_id", sa.UUID(), nullable=False),
        sa.Column("usuario_id", sa.UUID(), nullable=False),
        sa.Column("confirmado_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),

        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["aviso_id"], ["aviso.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["usuario_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "aviso_id", "usuario_id", name="uq_ack_aviso_tenant_usuario"),
    )
    op.create_index("ix_ack_aviso_tenant_id", "acknowledgment_aviso", ["tenant_id"], unique=False)


def downgrade() -> None:
    op.drop_table("acknowledgment_aviso")
    op.drop_table("aviso")
    op.execute("DROP TYPE IF EXISTS severidad_aviso")
    op.execute("DROP TYPE IF EXISTS alcance_aviso")

"""004_audit_log

Revision ID: 03dd2a3696a9
Revises: d4f8e2c9a1b0
Create Date: 2026-06-19 11:00:00.178704
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "03dd2a3696a9"
down_revision: Union[str, None] = "d4f8e2c9a1b0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -----------------------------------------------------------------------
    # 1. Crear tabla audit_log
    # -----------------------------------------------------------------------
    op.create_table(
        "audit_log",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("fecha_hora", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("actor_id", sa.UUID(), nullable=False),
        sa.Column("impersonado_id", sa.UUID(), nullable=True),
        sa.Column("materia_id", sa.UUID(), nullable=True, comment="FK futura → materia.id"),
        sa.Column("accion", sa.String(length=100), nullable=False, comment="Código de acción (ej: CALIFICACIONES_IMPORTAR)"),
        sa.Column("detalle", postgresql.JSONB, nullable=False),
        sa.Column("filas_afectadas", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("ip", sa.String(length=45), nullable=False, comment="Dirección IP del cliente"),
        sa.Column("user_agent", sa.Text(), nullable=False, server_default=sa.text("''")),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["actor_id"], ["user.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["impersonado_id"], ["user.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_log_tenant_fecha", "audit_log", ["tenant_id", "fecha_hora"], unique=False)
    op.create_index(op.f("ix_audit_log_tenant_id"), "audit_log", ["tenant_id"], unique=False)

    # -----------------------------------------------------------------------
    # 2. Reglas PostgreSQL para inmutabilidad DB-level
    # -----------------------------------------------------------------------
    op.execute(
        sa.text("CREATE RULE audit_log_no_update AS ON UPDATE TO audit_log DO INSTEAD NOTHING")
    )
    op.execute(
        sa.text("CREATE RULE audit_log_no_delete AS ON DELETE TO audit_log DO INSTEAD NOTHING")
    )


def downgrade() -> None:
    # -----------------------------------------------------------------------
    # 1. Eliminar tabla audit_log con CASCADE (incluye reglas e índices)
    #
    # Usamos DROP TABLE IF EXISTS ... CASCADE para ser robustos ante casos
    # donde la tabla fue eliminada externamente (ej: limpieza entre tests
    # de migración). CASCADE asegura que las reglas de inmutabilidad,
    # índices y FKs se eliminan junto con la tabla.
    # -----------------------------------------------------------------------
    op.execute(
        sa.text(
            "DROP TABLE IF EXISTS audit_log CASCADE"
        )
    )

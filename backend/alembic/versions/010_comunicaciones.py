"""010_comunicaciones

C-12: Crea la tabla ``comunicacion`` con tenant-scoping, cifrado del
destinatario, máquina de estados (Pendiente/Enviando/Enviado/Error/Cancelado)
y lote_id para agrupación de envíos masivos.

Revision ID: 010_comunicaciones
Revises: 009_calificacion_umbral_materia
Create Date: 2026-06-19 22:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "010_comunicaciones"
down_revision = "009_calificacion_umbral_materia"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "comunicacion",
        # TenantScopedMixin
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        # Columnas de dominio
        sa.Column("enviado_por", postgresql.UUID(as_uuid=True), nullable=False,
                  comment="FK → User que envía la comunicación"),
        sa.Column("materia_id", postgresql.UUID(as_uuid=True), nullable=True,
                  comment="FK → Materia (opcional)"),
        sa.Column("destinatario", sa.Text(), nullable=False,
                  comment="Email del destinatario (cifrado AES-256)"),
        sa.Column("destinatario_hash", sa.String(64), nullable=False,
                  comment="SHA-256 del email lowercase para búsqueda"),
        sa.Column("asunto", sa.Text(), nullable=False),
        sa.Column("cuerpo", sa.Text(), nullable=False),
        sa.Column("estado", sa.String(32), nullable=False,
                  server_default=sa.text("'Pendiente'"),
                  comment="Estado: Pendiente/Enviando/Enviado/Error/Cancelado"),
        sa.Column("lote_id", postgresql.UUID(as_uuid=True), nullable=True,
                  comment="UUID de lote para agrupación de envíos masivos"),
        sa.Column("requiere_aprobacion", sa.Boolean(), nullable=False,
                  server_default=sa.text("true"),
                  comment="Si true, requiere aprobación antes de enviar"),
        sa.Column("enviado_at", sa.DateTime(timezone=True), nullable=True,
                  comment="Timestamp del envío real"),
        # FKs
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["enviado_por"], ["user.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["materia_id"], ["materia.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Índices compuestos
    op.create_index(
        "ix_comunicacion_tenant_lote",
        "comunicacion",
        ["tenant_id", "lote_id"],
        unique=False,
    )
    op.create_index(
        "ix_comunicacion_tenant_estado",
        "comunicacion",
        ["tenant_id", "estado"],
        unique=False,
    )
    op.create_index(
        "ix_comunicacion_tenant_enviado_por",
        "comunicacion",
        ["tenant_id", "enviado_por"],
        unique=False,
    )
    op.create_index(
        "ix_comunicacion_tenant_destinatario_hash",
        "comunicacion",
        ["tenant_id", "destinatario_hash"],
        unique=False,
    )
    op.create_index(
        "ix_comunicacion_tenant_deleted",
        "comunicacion",
        ["tenant_id", "deleted_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_table("comunicacion")

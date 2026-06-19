"""007_perfil_y_mensajeria

C-20: Agrega columna modalidad_cobro a user.
Crea tablas hilo_mensaje y mensaje_interno con índices de aislamiento multi-tenant.

NO duplica columnas ya provistas por C-07 (006_usuarios_y_asignaciones):
    nombre, apellidos, banco, regional, legajo_profesional, facturador,
    dni_encrypted, cuil_encrypted, cbu_encrypted, alias_cbu_encrypted.

Este change agrega SOLO:
    - user.modalidad_cobro (nullable, 'factura' | 'liquidacion')
    - tabla hilo_mensaje
    - tabla mensaje_interno

Downgrade: DROP tablas + DROP columna modalidad_cobro (orden inverso).

Revision ID: 007_perfil_y_mensajeria
Revises: 006_usuarios_y_asignaciones
Create Date: 2026-06-19 00:00:00.000000
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "007_perfil_y_mensajeria"
down_revision = "006_usuarios_y_asignaciones"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # Fase 1: ALTER TABLE user — agregar modalidad_cobro
    # ------------------------------------------------------------------
    op.add_column(
        "user",
        sa.Column(
            "modalidad_cobro",
            sa.String(length=20),
            nullable=True,
            comment="Modalidad de cobro: 'factura' o 'liquidacion'",
        ),
    )

    # ------------------------------------------------------------------
    # Fase 2: CREATE TABLE hilo_mensaje
    # ------------------------------------------------------------------
    op.create_table(
        "hilo_mensaje",
        # TenantScopedMixin
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),

        # Campos propios
        sa.Column("asunto", sa.String(length=255), nullable=False,
                  comment="Asunto o título del hilo de conversación"),
        sa.Column("iniciado_por", postgresql.UUID(as_uuid=True), nullable=False,
                  comment="FK al User que inició el hilo (del JWT)"),
        sa.Column("destinatario_id", postgresql.UUID(as_uuid=True), nullable=False,
                  comment="FK al User destinatario del hilo"),

        # Constraints
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["iniciado_por"], ["user.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["destinatario_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Índices de aislamiento
    op.create_index(
        "ix_hilo_mensaje_tenant_destinatario",
        "hilo_mensaje",
        ["tenant_id", "destinatario_id"],
        unique=False,
    )
    op.create_index(
        "ix_hilo_mensaje_tenant_iniciado_por",
        "hilo_mensaje",
        ["tenant_id", "iniciado_por"],
        unique=False,
    )
    op.create_index(
        "ix_hilo_mensaje_tenant_deleted",
        "hilo_mensaje",
        ["tenant_id", "deleted_at"],
        unique=False,
    )

    # ------------------------------------------------------------------
    # Fase 3: CREATE TABLE mensaje_interno
    # ------------------------------------------------------------------
    op.create_table(
        "mensaje_interno",
        # TenantScopedMixin
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),

        # Campos propios
        sa.Column("hilo_id", postgresql.UUID(as_uuid=True), nullable=False,
                  comment="FK al HiloMensaje"),
        sa.Column("autor_id", postgresql.UUID(as_uuid=True), nullable=False,
                  comment="FK al User autor (del JWT)"),
        sa.Column("cuerpo", sa.Text(), nullable=False,
                  comment="Cuerpo del mensaje"),
        sa.Column(
            "creado_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Timestamp de creación del mensaje",
        ),
        sa.Column("leido_at", sa.DateTime(timezone=True), nullable=True,
                  comment="Timestamp de lectura; NULL = no leído"),

        # Constraints
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["hilo_id"], ["hilo_mensaje.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["autor_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Índices de aislamiento
    op.create_index(
        "ix_mensaje_interno_tenant_hilo",
        "mensaje_interno",
        ["tenant_id", "hilo_id"],
        unique=False,
    )
    op.create_index(
        "ix_mensaje_interno_tenant_deleted",
        "mensaje_interno",
        ["tenant_id", "deleted_at"],
        unique=False,
    )


def downgrade() -> None:
    # DROP índices de mensaje_interno
    op.drop_index("ix_mensaje_interno_tenant_deleted", table_name="mensaje_interno")
    op.drop_index("ix_mensaje_interno_tenant_hilo", table_name="mensaje_interno")

    # DROP tabla mensaje_interno
    op.drop_table("mensaje_interno")

    # DROP índices de hilo_mensaje
    op.drop_index("ix_hilo_mensaje_tenant_deleted", table_name="hilo_mensaje")
    op.drop_index("ix_hilo_mensaje_tenant_iniciado_por", table_name="hilo_mensaje")
    op.drop_index("ix_hilo_mensaje_tenant_destinatario", table_name="hilo_mensaje")

    # DROP tabla hilo_mensaje
    op.drop_table("hilo_mensaje")

    # DROP columna modalidad_cobro de user
    op.drop_column("user", "modalidad_cobro")

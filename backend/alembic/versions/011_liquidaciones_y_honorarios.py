"""011_liquidaciones_y_honorarios

C-18: Crea las tablas salario_base, salario_plus, liquidacion y factura
para la gestión de honorarios docentes con multi-tenancy row-level.

Revision ID: 011_liquidaciones_y_honorarios
Revises: 010_comunicaciones
Create Date: 2026-06-19 23:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "011_liquidaciones_y_honorarios"
down_revision = "010_comunicaciones"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ─── salario_base ─────────────────────────────────────────────────────
    op.create_table(
        "salario_base",
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
        # Columnas de dominio
        sa.Column(
            "rol",
            sa.String(32),
            nullable=False,
            comment="Rol docente (PROFESOR, TUTOR, COORDINADOR, NEXO)",
        ),
        sa.Column(
            "monto",
            sa.Numeric(12, 2),
            nullable=False,
            comment="Monto base mensual",
        ),
        sa.Column(
            "desde",
            sa.Date(),
            nullable=False,
            comment="Inicio de vigencia (inclusive)",
        ),
        sa.Column(
            "hasta",
            sa.Date(),
            nullable=True,
            comment="Fin de vigencia (inclusive); NULL = abierto",
        ),
        # Constraints
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_salario_base_tenant_rol_vigencia",
        "salario_base",
        ["tenant_id", "rol", "desde", "hasta"],
        unique=False,
    )
    op.create_index(
        "ix_salario_base_tenant_deleted",
        "salario_base",
        ["tenant_id", "deleted_at"],
        unique=False,
    )

    # ─── salario_plus ─────────────────────────────────────────────────────
    op.create_table(
        "salario_plus",
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
        # Columnas de dominio
        sa.Column(
            "grupo",
            sa.String(32),
            nullable=False,
            comment="Clave del plus (PROG, BD, ARQ, MAT, MET u otras)",
        ),
        sa.Column(
            "rol",
            sa.String(32),
            nullable=False,
            comment="Rol docente al que aplica este plus",
        ),
        sa.Column(
            "descripcion",
            sa.Text(),
            nullable=False,
            comment="Descripción legible del plus",
        ),
        sa.Column(
            "monto",
            sa.Numeric(12, 2),
            nullable=False,
            comment="Monto del plus mensual",
        ),
        sa.Column(
            "desde",
            sa.Date(),
            nullable=False,
            comment="Inicio de vigencia (inclusive)",
        ),
        sa.Column(
            "hasta",
            sa.Date(),
            nullable=True,
            comment="Fin de vigencia (inclusive); NULL = abierto",
        ),
        # Constraints
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_salario_plus_tenant_grupo_rol_vigencia",
        "salario_plus",
        ["tenant_id", "grupo", "rol", "desde", "hasta"],
        unique=False,
    )
    op.create_index(
        "ix_salario_plus_tenant_deleted",
        "salario_plus",
        ["tenant_id", "deleted_at"],
        unique=False,
    )

    # ─── liquidacion ──────────────────────────────────────────────────────
    op.create_table(
        "liquidacion",
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
        # Columnas de dominio
        sa.Column(
            "cohorte_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment="FK → Cohorte",
        ),
        sa.Column(
            "periodo",
            sa.String(7),
            nullable=False,
            comment="Período AAAA-MM",
        ),
        sa.Column(
            "usuario_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment="UUID del docente liquidado",
        ),
        sa.Column(
            "rol",
            sa.String(32),
            nullable=False,
            comment="Rol del docente en el período",
        ),
        sa.Column(
            "comisiones",
            postgresql.ARRAY(sa.String()),
            nullable=False,
            server_default=sa.text("'{}'"),
            comment="IDs de comisiones del docente",
        ),
        sa.Column(
            "monto_base",
            sa.Numeric(12, 2),
            nullable=False,
            server_default=sa.text("0"),
            comment="Monto base según grilla salarial",
        ),
        sa.Column(
            "monto_plus",
            sa.Numeric(12, 2),
            nullable=False,
            server_default=sa.text("0"),
            comment="Suma de plus aplicados",
        ),
        sa.Column(
            "total",
            sa.Numeric(12, 2),
            nullable=False,
            server_default=sa.text("0"),
            comment="Total = monto_base + monto_plus",
        ),
        sa.Column(
            "es_nexo",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
            comment="True si el rol es NEXO",
        ),
        sa.Column(
            "excluido_por_factura",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
            comment="True si el docente es facturador",
        ),
        sa.Column(
            "estado",
            sa.String(16),
            nullable=False,
            server_default=sa.text("'Abierta'"),
            comment="Estado: Abierta | Cerrada",
        ),
        # Constraints
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["cohorte_id"], ["cohorte.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["usuario_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_liquidacion_tenant_cohorte_periodo",
        "liquidacion",
        ["tenant_id", "cohorte_id", "periodo"],
        unique=False,
    )
    op.create_index(
        "ix_liquidacion_tenant_usuario_periodo",
        "liquidacion",
        ["tenant_id", "usuario_id", "periodo"],
        unique=False,
    )
    op.create_index(
        "ix_liquidacion_tenant_deleted",
        "liquidacion",
        ["tenant_id", "deleted_at"],
        unique=False,
    )

    # ─── factura ──────────────────────────────────────────────────────────
    op.create_table(
        "factura",
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
        # Columnas de dominio
        sa.Column(
            "usuario_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment="UUID del docente facturador",
        ),
        sa.Column(
            "periodo",
            sa.String(7),
            nullable=False,
            comment="Período AAAA-MM",
        ),
        sa.Column(
            "detalle",
            sa.Text(),
            nullable=False,
            comment="Descripción del servicio facturado",
        ),
        sa.Column(
            "referencia_archivo",
            sa.String(512),
            nullable=False,
            comment="Nombre o path del archivo adjunto",
        ),
        sa.Column(
            "tamano_kb",
            sa.Numeric(10, 2),
            nullable=False,
            comment="Tamaño del archivo en KB",
        ),
        sa.Column(
            "estado",
            sa.String(16),
            nullable=False,
            server_default=sa.text("'Pendiente'"),
            comment="Estado: Pendiente | Abonada",
        ),
        sa.Column(
            "cargada_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Timestamp de carga",
        ),
        sa.Column(
            "abonada_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Timestamp de pago; NULL si Pendiente",
        ),
        # Constraints
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["usuario_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_factura_tenant_periodo",
        "factura",
        ["tenant_id", "periodo"],
        unique=False,
    )
    op.create_index(
        "ix_factura_tenant_usuario_periodo",
        "factura",
        ["tenant_id", "usuario_id", "periodo"],
        unique=False,
    )
    op.create_index(
        "ix_factura_tenant_deleted",
        "factura",
        ["tenant_id", "deleted_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_table("factura")
    op.drop_table("liquidacion")
    op.drop_table("salario_plus")
    op.drop_table("salario_base")

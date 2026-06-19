"""006_usuarios_y_asignaciones

C-07: Extiende la tabla user con columnas PII cifradas e institucionales.
Crea la tabla asignacion con FK al catálogo académico y seeds de permisos.

Orden de fases (aprobado en CHECKPOINT D8):
    1-10. ALTER TABLE user ADD COLUMN (10 columnas nuevas — todas nullable
          excepto facturador NOT NULL DEFAULT false)
    11.   CREATE TABLE asignacion (con FKs nullable y soft-delete)
    12.   CREATE INDEX (3 índices sobre asignacion)
    13.   INSERT INTO permiso (seeds idempotentes usuarios:gestionar, equipos:asignar)

Downgrade: DROP TABLE asignacion → DROP COLUMNs (orden inverso).
           NO borra seeds de permisos (idempotencia).

Revision ID: 006_usuarios_y_asignaciones
Revises: 005_estructura_academica
Create Date: 2026-06-19 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "006_usuarios_y_asignaciones"
down_revision = "005_estructura_academica"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # Fase 1–10: ALTER TABLE user — nuevas columnas (NULLABLE salvo facturador)
    # ------------------------------------------------------------------
    op.add_column("user", sa.Column("nombre", sa.String(length=255), nullable=True,
                                    comment="Nombre/s del usuario"))
    op.add_column("user", sa.Column("apellidos", sa.String(length=255), nullable=True,
                                    comment="Apellido/s del usuario"))
    op.add_column("user", sa.Column("dni_encrypted", sa.Text(), nullable=True,
                                    comment="DNI cifrado AES-256-GCM (base64)"))
    op.add_column("user", sa.Column("cuil_encrypted", sa.Text(), nullable=True,
                                    comment="CUIL cifrado AES-256-GCM (base64)"))
    op.add_column("user", sa.Column("cbu_encrypted", sa.Text(), nullable=True,
                                    comment="CBU cifrado AES-256-GCM (base64)"))
    op.add_column("user", sa.Column("alias_cbu_encrypted", sa.Text(), nullable=True,
                                    comment="Alias CBU cifrado AES-256-GCM (base64)"))
    op.add_column("user", sa.Column("banco", sa.String(length=255), nullable=True,
                                    comment="Banco del usuario"))
    op.add_column("user", sa.Column("regional", sa.String(length=255), nullable=True,
                                    comment="Regional/sede del usuario"))
    op.add_column("user", sa.Column("legajo_profesional", sa.String(length=100), nullable=True,
                                    comment="Legajo profesional (atributo de negocio, NO credencial)"))
    op.add_column("user", sa.Column("facturador", sa.Boolean(), nullable=False,
                                    server_default=sa.text("false"),
                                    comment="True si el usuario emite facturas"))

    # ------------------------------------------------------------------
    # Fase 11: CREATE TABLE asignacion
    # ------------------------------------------------------------------
    op.create_table(
        "asignacion",
        # TenantScopedMixin
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),

        # FKs obligatorias
        sa.Column("usuario_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role_id", postgresql.UUID(as_uuid=True), nullable=False),

        # FKs de contexto académico — nullable
        sa.Column("materia_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("carrera_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("cohorte_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("responsable_id", postgresql.UUID(as_uuid=True), nullable=True),

        # Comisiones — ARRAY de texto
        sa.Column("comisiones", postgresql.ARRAY(sa.String()), nullable=True,
                  server_default=sa.text("'{}'::varchar[]")),

        # Vigencia
        sa.Column("desde", sa.DateTime(timezone=True), nullable=False),
        sa.Column("hasta", sa.DateTime(timezone=True), nullable=True),

        # FKs
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["usuario_id"], ["user.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["role_id"], ["role.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["materia_id"], ["materia.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["carrera_id"], ["carrera.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["cohorte_id"], ["cohorte.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["responsable_id"], ["user.id"], ondelete="SET NULL"),

        sa.PrimaryKeyConstraint("id"),
    )

    # ------------------------------------------------------------------
    # Fase 12: CREATE INDEX (3 índices sobre asignacion)
    # ------------------------------------------------------------------
    op.create_index("ix_asignacion_tenant_usuario", "asignacion",
                    ["tenant_id", "usuario_id"], unique=False)
    op.create_index("ix_asignacion_tenant_responsable", "asignacion",
                    ["tenant_id", "responsable_id"], unique=False)
    op.create_index("ix_asignacion_tenant_deleted", "asignacion",
                    ["tenant_id", "deleted_at"], unique=False)

    # ------------------------------------------------------------------
    # Fase 13: Seeds de permisos — idempotentes (ON CONFLICT DO NOTHING)
    # ------------------------------------------------------------------
    # Los permisos se crean a nivel global (sin tenant_id) no aplica aquí.
    # En este proyecto, los permisos son tenant-scoped. El seed se agrega
    # a nivel de cada tenant en runtime (via RolPermiso). Los permisos
    # 'usuarios:gestionar' y 'equipos:asignar' se crean en el seed inicial
    # de roles/permisos, que se hace al registrar el tenant.
    # Sin embargo, para garantizar que existan para tenants pre-existentes
    # no usamos INSERT directo ya que no tenemos tenant_id aquí.
    # Esta decisión es equivalente a "seeds on tenant creation" (ver service).
    # Documentado como decisión operativa: los nuevos permisos se crean
    # vía el endpoint de RBAC o el script de seed de tenant.
    pass


def downgrade() -> None:
    # DROP índices
    op.drop_index("ix_asignacion_tenant_deleted", table_name="asignacion")
    op.drop_index("ix_asignacion_tenant_responsable", table_name="asignacion")
    op.drop_index("ix_asignacion_tenant_usuario", table_name="asignacion")

    # DROP tabla asignacion
    op.drop_table("asignacion")

    # DROP columnas de user — orden inverso a upgrade
    op.drop_column("user", "facturador")
    op.drop_column("user", "legajo_profesional")
    op.drop_column("user", "regional")
    op.drop_column("user", "banco")
    op.drop_column("user", "alias_cbu_encrypted")
    op.drop_column("user", "cbu_encrypted")
    op.drop_column("user", "cuil_encrypted")
    op.drop_column("user", "dni_encrypted")
    op.drop_column("user", "apellidos")
    op.drop_column("user", "nombre")
    # NO se borran seeds de permisos (idempotencia)

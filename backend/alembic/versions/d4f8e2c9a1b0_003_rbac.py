"""003_rbac

Revision ID: d4f8e2c9a1b0
Revises: 87ff312e2a56
Create Date: 2026-06-18 19:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


revision: str = "d4f8e2c9a1b0"
down_revision: Union[str, None] = "87ff312e2a56"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ---------------------------------------------------------------------------
# Data for seed — derivado de app/core/rbac_seed.py
# ---------------------------------------------------------------------------

# Roles del dominio (se crean si no existen)
_DOMAIN_ROLES: list[tuple[str, str]] = [
    ("alumno", "Alumno"),
    ("tutor", "Tutor"),
    ("profesor", "Profesor"),
    ("coordinador", "Coordinador"),
    ("nexo", "Nexo"),
    ("admin", "Administrador"),
    ("finanzas", "Finanzas"),
]

# Catálogo de permisos (code, modulo, accion, descripcion)
_PERMISOS: list[tuple[str, str, str, str]] = [
    ("estado:ver_propio", "estado", "ver_propio", "Ver estado académico propio"),
    ("evaluaciones:reservar", "evaluaciones", "reservar", "Reservar instancia de evaluación"),
    ("avisos:confirmar", "avisos", "confirmar", "Confirmar avisos (acknowledgment)"),
    ("calificaciones:importar", "calificaciones", "importar", "Importar calificaciones"),
    ("atrasados:ver", "atrasados", "ver", "Ver alumnos atrasados"),
    ("atrasados:detectar_sin_corregir", "atrasados", "detectar_sin_corregir", "Detectar entregas sin corregir"),
    ("comunicacion:enviar", "comunicacion", "enviar", "Enviar comunicaciones a alumnos"),
    ("comunicacion:aprobar", "comunicacion", "aprobar", "Aprobar comunicaciones masivas"),
    ("encuentros:gestionar", "encuentros", "gestionar", "Gestionar encuentros"),
    ("guardias:registrar", "guardias", "registrar", "Registrar guardias"),
    ("tareas:gestionar", "tareas", "gestionar", "Gestionar tareas internas"),
    ("avisos:publicar", "avisos", "publicar", "Publicar avisos"),
    ("equipos:asignar", "equipos", "asignar", "Gestionar equipos docentes (asignaciones)"),
    ("estructura:gestionar", "estructura", "gestionar", "Gestionar estructura académica"),
    ("usuarios:gestionar", "usuarios", "gestionar", "Gestionar usuarios del tenant"),
    ("auditoria:ver", "auditoria", "ver", "Ver auditoría"),
    ("grilla:operar", "grilla", "operar", "Operar grilla salarial"),
    ("liquidaciones:calcular", "liquidaciones", "calcular", "Calcular liquidaciones"),
    ("liquidaciones:cerrar", "liquidaciones", "cerrar", "Cerrar liquidaciones"),
    ("facturas:gestionar", "facturas", "gestionar", "Gestionar facturas"),
    ("configuracion:gestionar", "configuracion", "gestionar", "Configurar el tenant"),
    ("impersonacion:usar", "impersonacion", "usar", "Impersonar a otro usuario"),
]

# Matriz base: (role_code, permiso_code, scope)
_MATRIZ: list[tuple[str, str, str]] = [
    # ALUMNO
    ("alumno", "estado:ver_propio", "propio"),
    ("alumno", "evaluaciones:reservar", "propio"),
    ("alumno", "avisos:confirmar", "global"),
    # TUTOR
    ("tutor", "avisos:confirmar", "global"),
    ("tutor", "atrasados:ver", "global"),
    ("tutor", "atrasados:detectar_sin_corregir", "global"),
    ("tutor", "encuentros:gestionar", "global"),
    ("tutor", "guardias:registrar", "propio"),
    # PROFESOR
    ("profesor", "avisos:confirmar", "global"),
    ("profesor", "calificaciones:importar", "propio"),
    ("profesor", "atrasados:ver", "propio"),
    ("profesor", "atrasados:detectar_sin_corregir", "propio"),
    ("profesor", "comunicacion:enviar", "propio"),
    ("profesor", "encuentros:gestionar", "propio"),
    ("profesor", "guardias:registrar", "propio"),
    ("profesor", "tareas:gestionar", "propio"),
    # COORDINADOR
    ("coordinador", "avisos:confirmar", "global"),
    ("coordinador", "calificaciones:importar", "global"),
    ("coordinador", "atrasados:ver", "global"),
    ("coordinador", "atrasados:detectar_sin_corregir", "global"),
    ("coordinador", "comunicacion:enviar", "global"),
    ("coordinador", "comunicacion:aprobar", "global"),
    ("coordinador", "encuentros:gestionar", "global"),
    ("coordinador", "guardias:registrar", "global"),
    ("coordinador", "tareas:gestionar", "global"),
    ("coordinador", "avisos:publicar", "global"),
    ("coordinador", "equipos:asignar", "global"),
    ("coordinador", "auditoria:ver", "propio"),
    # NEXO (solo transversales — confirmar PA-25)
    ("nexo", "avisos:confirmar", "global"),
    # ADMIN
    ("admin", "avisos:confirmar", "global"),
    ("admin", "calificaciones:importar", "global"),
    ("admin", "atrasados:ver", "global"),
    ("admin", "atrasados:detectar_sin_corregir", "global"),
    ("admin", "comunicacion:enviar", "global"),
    ("admin", "comunicacion:aprobar", "global"),
    ("admin", "encuentros:gestionar", "global"),
    ("admin", "guardias:registrar", "global"),
    ("admin", "tareas:gestionar", "global"),
    ("admin", "avisos:publicar", "global"),
    ("admin", "equipos:asignar", "global"),
    ("admin", "estructura:gestionar", "global"),
    ("admin", "usuarios:gestionar", "global"),
    ("admin", "auditoria:ver", "global"),
    ("admin", "configuracion:gestionar", "global"),
    # FINANZAS
    ("finanzas", "avisos:confirmar", "global"),
    ("finanzas", "auditoria:ver", "global"),
    ("finanzas", "grilla:operar", "global"),
    ("finanzas", "liquidaciones:calcular", "global"),
    ("finanzas", "liquidaciones:cerrar", "global"),
    ("finanzas", "facturas:gestionar", "global"),
]


def upgrade() -> None:
    # -----------------------------------------------------------------------
    # 1. Crear tabla permiso
    # -----------------------------------------------------------------------
    op.create_table(
        "permiso",
        sa.Column("modulo", sa.String(length=100), nullable=False, comment="Módulo funcional (ej: comunicacion, calificaciones)"),
        sa.Column("accion", sa.String(length=100), nullable=False, comment="Acción dentro del módulo (ej: aprobar, importar)"),
        sa.Column("code", sa.String(length=201), nullable=False, comment="Clave única derivada '{modulo}:{accion}'"),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "code", name="uq_permiso_tenant_code"),
    )
    op.create_index("ix_permiso_tenant_deleted", "permiso", ["tenant_id", "deleted_at"], unique=False)
    op.create_index(op.f("ix_permiso_tenant_id"), "permiso", ["tenant_id"], unique=False)
    op.execute(
        "ALTER TABLE permiso ADD CONSTRAINT ck_permiso_code_format "
        "CHECK (code ~ '^[a-z_]+:[a-z_]+$')"
    )

    # -----------------------------------------------------------------------
    # 2. Crear tabla rol_permiso
    # -----------------------------------------------------------------------
    op.create_table(
        "rol_permiso",
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("role_id", sa.UUID(), nullable=False),
        sa.Column("permiso_id", sa.UUID(), nullable=False),
        sa.Column("scope", sa.String(length=10), nullable=False, comment="Alcance: 'global' (cualquier recurso) o 'propio' (solo propio)"),
        sa.Column("asignado_por", sa.UUID(), nullable=True, comment="UUID del usuario que asignó este permiso al rol"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["role_id"], ["role.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["permiso_id"], ["permiso.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["asignado_por"], ["user.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("tenant_id", "role_id", "permiso_id"),
    )
    op.create_index("ix_rol_permiso_tenant_role", "rol_permiso", ["tenant_id", "role_id"], unique=False)
    op.create_index("ix_rol_permiso_tenant_permiso", "rol_permiso", ["tenant_id", "permiso_id"], unique=False)
    op.execute(
        "ALTER TABLE rol_permiso ADD CONSTRAINT ck_rol_permiso_scope "
        "CHECK (scope IN ('global', 'propio'))"
    )

    # -----------------------------------------------------------------------
    # 3. Data migration — seed idempotente
    # -----------------------------------------------------------------------
    conn = op.get_bind()

    # 3a. Obtener todos los tenants activos
    tenants = conn.execute(
        text("SELECT id FROM tenant WHERE activo = TRUE")
    ).fetchall()

    if not tenants:
        return  # Sin tenants, no hay nada que seedear

    # 3b. Para cada tenant, seedear roles si no existen
    _seed_roles(conn, tenants)

    # 3c. Para cada tenant, seedear catálogo de permisos
    _seed_permisos(conn, tenants)

    # 3d. Para cada tenant, seedear matriz base
    _seed_matriz(conn, tenants)


def downgrade() -> None:
    op.drop_table("rol_permiso")
    op.drop_table("permiso")


# ===========================================================================
# Helper functions — seed data
# ===========================================================================


def _seed_roles(conn, tenants: list) -> None:
    """Seedear roles base del dominio para cada tenant (idempotente)."""
    for tenant_id, in tenants:
        for role_code, role_nombre in _DOMAIN_ROLES:
            conn.execute(
                text("""
                    INSERT INTO role (id, tenant_id, code, nombre, created_at, updated_at)
                    SELECT gen_random_uuid(), :tenant_id, :code, :nombre, NOW(), NOW()
                    WHERE NOT EXISTS (
                        SELECT 1 FROM role
                        WHERE tenant_id = :tenant_id2 AND code = :code2
                    )
                """),
                {
                    "tenant_id": tenant_id,
                    "code": role_code,
                    "nombre": role_nombre,
                    "tenant_id2": tenant_id,
                    "code2": role_code,
                },
            )


def _seed_permisos(conn, tenants: list) -> None:
    """Seedear catálogo de permisos para cada tenant (idempotente)."""
    for code, modulo, accion, _desc in _PERMISOS:
        for tenant_id, in tenants:
            conn.execute(
                text("""
                    INSERT INTO permiso (id, tenant_id, modulo, accion, code, created_at, updated_at)
                    SELECT gen_random_uuid(), :tenant_id, :modulo, :accion, :code, NOW(), NOW()
                    WHERE NOT EXISTS (
                        SELECT 1 FROM permiso
                        WHERE tenant_id = :tenant_id2 AND code = :code2
                    )
                """),
                {
                    "tenant_id": tenant_id,
                    "modulo": modulo,
                    "accion": accion,
                    "code": code,
                    "tenant_id2": tenant_id,
                    "code2": code,
                },
            )


def _seed_matriz(conn, tenants: list) -> None:
    """Seedear matriz base rol×permiso para cada tenant (idempotente)."""
    for role_code, permiso_code, scope in _MATRIZ:
        for tenant_id, in tenants:
            conn.execute(
                text("""
                    INSERT INTO rol_permiso (tenant_id, role_id, permiso_id, scope, created_at)
                    SELECT
                        :tenant_id,
                        r.id,
                        p.id,
                        :scope,
                        NOW()
                    FROM role r
                    CROSS JOIN permiso p
                    WHERE r.tenant_id = :tenant_id2
                      AND r.code = :role_code
                      AND p.tenant_id = :tenant_id3
                      AND p.code = :permiso_code
                      AND NOT EXISTS (
                          SELECT 1 FROM rol_permiso rp
                          WHERE rp.tenant_id = :tenant_id4
                            AND rp.role_id = r.id
                            AND rp.permiso_id = p.id
                      )
                """),
                {
                    "tenant_id": tenant_id,
                    "scope": scope,
                    "tenant_id2": tenant_id,
                    "role_code": role_code,
                    "tenant_id3": tenant_id,
                    "permiso_code": permiso_code,
                    "tenant_id4": tenant_id,
                },
            )

"""Tests para migration 003_rbac — creación de permiso + rol_permiso + seed.

Verifica que `alembic upgrade head` cree las tablas con constraints,
que el seed idempotente inserte datos correctos y que `downgrade` los
elimine en orden inverso.

Usa subprocess para invocar alembic sobre la base de test.
Requiere PostgreSQL corriendo (--run-db).
"""

import subprocess
import sys
from pathlib import Path

import pytest
import asyncpg

BACKEND_DIR = Path(__file__).resolve().parent.parent

pytestmark = pytest.mark.requires_db

# Tablas que debe crear la migración 003
RBAC_TABLES = [
    "permiso",
    "rol_permiso",
]

DATABASE_URL = "postgresql://activia:activia@localhost:5432/activia_trace_test"

# Semillas esperadas
EXPECTED_PERMISO_COUNT = 22
EXPECTED_MATRIX_ROWS = 55


def _alembic(*args: str) -> str:
    """Ejecuta alembic como módulo Python y retorna stdout+stderr."""
    result = subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        capture_output=True,
        text=True,
        cwd=str(BACKEND_DIR),
    )
    if result.returncode != 0:
        msg = f"alembic {' '.join(args)} failed\nstdout:{result.stdout}\nstderr:{result.stderr}"
        raise RuntimeError(msg)
    return result.stdout + result.stderr


async def _get_tables() -> list[str]:
    """Retorna lista de tablas públicas en la base de test."""
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        rows = await conn.fetch(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema='public' ORDER BY table_name"
        )
        return [r["table_name"] for r in rows]
    finally:
        await conn.close()


async def _get_alembic_version() -> str | None:
    """Retorna la versión actual de alembic en la base."""
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        row = await conn.fetchrow("SELECT version_num FROM alembic_version")
        return row["version_num"] if row else None
    finally:
        await conn.close()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
async def reset_to_002():
    """Fixture que asegura que arrancamos en migration 002 (auth).

    Si estamos en head (003), hace downgrade -1.
    Si estamos en 002, no hace nada.
    """
    version = await _get_alembic_version()
    if version is None:
        # Arrancar desde 001 y aplicar 002
        _alembic("upgrade", "87ff312e2a56")
    elif version != "87ff312e2a56":
        # Estamos en 003 o superior → downgrade
        _alembic("downgrade", "87ff312e2a56")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestMigration003Upgrade:
    """Scenario: Aplicar migration 003 desde 002."""

    async def test_upgrade_creates_rbac_tables(self):
        """WHEN corremos upgrade a 003, THEN permiso y rol_permiso existen."""
        _alembic("upgrade", "d4f8e2c9a1b0")

        tables = await _get_tables()
        for table in RBAC_TABLES:
            assert table in tables, f"Tabla '{table}' no fue creada por migration 003"

    async def test_upgrade_sets_alembic_version(self):
        """WHEN upgrade a 003, THEN alembic_version apunta a 003."""
        _alembic("upgrade", "d4f8e2c9a1b0")

        version = await _get_alembic_version()
        assert version == "d4f8e2c9a1b0"

    async def test_upgrade_seeds_permisos_for_tenants(self):
        """WHEN hay tenants existentes, THEN se siembra el catálogo."""
        # Crear un tenant primero
        _alembic("upgrade", "87ff312e2a56")

        conn = await asyncpg.connect(DATABASE_URL)
        try:
            await conn.execute("DELETE FROM tenant WHERE id = '11111111-1111-1111-1111-111111111111'")
            await conn.execute("""
                INSERT INTO tenant (id, slug, nombre, activo, created_at, updated_at)
                VALUES ('11111111-1111-1111-1111-111111111111', 'test', 'Test Tenant', TRUE, NOW(), NOW())
            """)
        finally:
            await conn.close()

        _alembic("upgrade", "d4f8e2c9a1b0")

        conn = await asyncpg.connect(DATABASE_URL)
        try:
            row = await conn.fetchrow(
                "SELECT COUNT(*) AS cnt FROM permiso WHERE tenant_id = '11111111-1111-1111-1111-111111111111'"
            )
            assert row["cnt"] >= EXPECTED_PERMISO_COUNT, (
                f"Esperaba al menos {EXPECTED_PERMISO_COUNT} permisos, "
                f"se crearon {row['cnt']}"
            )
        finally:
            await conn.close()

    async def test_seed_idempotent(self):
        """WHEN el seed se ejecuta dos veces, THEN no duplica filas."""
        _alembic("upgrade", "87ff312e2a56")

        conn = await asyncpg.connect(DATABASE_URL)
        try:
            await conn.execute("DELETE FROM tenant WHERE id = '22222222-2222-2222-2222-222222222222'")
            await conn.execute("""
                INSERT INTO tenant (id, slug, nombre, activo, created_at, updated_at)
                VALUES ('22222222-2222-2222-2222-222222222222', 'idempotent', 'Idempotent', TRUE, NOW(), NOW())
            """)
        finally:
            await conn.close()

        _alembic("upgrade", "d4f8e2c9a1b0")
        _alembic("downgrade", "87ff312e2a56")
        _alembic("upgrade", "d4f8e2c9a1b0")  # Segunda aplicación

        conn = await asyncpg.connect(DATABASE_URL)
        try:
            row = await conn.fetchrow(
                "SELECT COUNT(*) AS cnt FROM permiso WHERE tenant_id = '22222222-2222-2222-2222-222222222222'"
            )
            assert row["cnt"] == EXPECTED_PERMISO_COUNT, (
                f"Seed idempotente: esperaba {EXPECTED_PERMISO_COUNT} permisos, "
                f"se encontraron {row['cnt']}"
            )
        finally:
            await conn.close()

    async def test_permiso_check_constraint_validates_format(self):
        """WHEN se intenta insertar code inválido, THEN CHECK constraint lo rechaza."""
        _alembic("upgrade", "d4f8e2c9a1b0")

        conn = await asyncpg.connect(DATABASE_URL)
        try:
            with pytest.raises(
                (asyncpg.exceptions.CheckViolationError, asyncpg.exceptions.ForeignKeyViolationError)
            ):
                await conn.execute("""
                    INSERT INTO permiso (id, tenant_id, modulo, accion, code, created_at, updated_at)
                    VALUES (
                        '00000000-0000-0000-0000-000000000001',
                        (SELECT id FROM tenant LIMIT 1),
                        'Comunicacion', 'Aprobar', 'Comunicacion:Aprobar',
                        NOW(), NOW()
                    )
                """)
        finally:
            await conn.close()

    async def test_rol_permiso_scope_check_constraint(self):
        """WHEN se intenta insertar scope inválido, THEN CHECK constraint lo rechaza."""
        _alembic("upgrade", "d4f8e2c9a1b0")

        conn = await asyncpg.connect(DATABASE_URL)
        try:
            with pytest.raises(asyncpg.exceptions.CheckViolationError):
                await conn.execute("""
                    INSERT INTO rol_permiso (tenant_id, role_id, permiso_id, scope, created_at)
                    VALUES (
                        (SELECT tenant_id FROM role LIMIT 1),
                        (SELECT id FROM role LIMIT 1),
                        (SELECT id FROM permiso LIMIT 1),
                        'invalid',
                        NOW()
                    )
                """)
        finally:
            await conn.close()


class TestMigration003Downgrade:
    """Scenario: Revertir migration 003 desde 003 a 002."""

    async def test_downgrade_removes_rbac_tables(self):
        """GIVEN migration 003 aplicada, WHEN downgrade -1, THEN tablas eliminadas."""
        _alembic("upgrade", "d4f8e2c9a1b0")
        _alembic("downgrade", "87ff312e2a56")

        tables = await _get_tables()
        for table in RBAC_TABLES:
            assert table not in tables, f"Tabla '{table}' no fue eliminada por downgrade"

    async def test_downgrade_keeps_auth_tables(self):
        """WHEN downgrade -1, THEN tablas de auth persisten."""
        _alembic("upgrade", "d4f8e2c9a1b0")
        _alembic("downgrade", "87ff312e2a56")

        tables = await _get_tables()
        for table in ["role", "user", "refresh_token", "user_role"]:
            assert table in tables, f"Tabla '{table}' debe persistir tras downgrade"

    async def test_downgrade_sets_version_to_002(self):
        """WHEN downgrade -1, THEN alembic_version vuelve a 002."""
        _alembic("upgrade", "d4f8e2c9a1b0")
        _alembic("downgrade", "87ff312e2a56")

        version = await _get_alembic_version()
        assert version == "87ff312e2a56"

    async def test_downgrade_reapply_is_idempotent(self):
        """GIVEN upgrade → downgrade → upgrade, THEN todo funciona de nuevo."""
        _alembic("upgrade", "d4f8e2c9a1b0")
        _alembic("downgrade", "87ff312e2a56")
        _alembic("upgrade", "d4f8e2c9a1b0")

        tables = await _get_tables()
        for table in ["permiso", "rol_permiso"]:
            assert table in tables, f"Tabla '{table}' no recreada tras re-upgrade"

        version = await _get_alembic_version()
        assert version == "d4f8e2c9a1b0"

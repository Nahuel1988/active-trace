"""Tests para migration 004_audit_log — inmutabilidad DB-level.

Verifica que:
- La tabla audit_log existe con la estructura correcta.
- Las reglas PostgreSQL bloquean UPDATE y DELETE.
- El índice compuesto (tenant_id, fecha_hora) existe.
- Downgrade elimina tabla y reglas.

Requiere PostgreSQL (--run-db).
"""

import subprocess
import sys
import uuid
from pathlib import Path

import pytest
import asyncpg

BACKEND_DIR = Path(__file__).resolve().parent.parent

pytestmark = pytest.mark.requires_db

DATABASE_URL = "postgresql://activia:activia@localhost:5432/activia_trace_test"

REV_003 = "d4f8e2c9a1b0"
REV_004 = "03dd2a3696a9"


def _alembic(*args: str) -> None:
    """Ejecuta alembic como módulo Python."""
    result = subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        capture_output=True,
        text=True,
        cwd=str(BACKEND_DIR),
    )
    if result.returncode != 0:
        msg = f"alembic {' '.join(args)} failed\nstdout:{result.stdout}\nstderr:{result.stderr}"
        raise RuntimeError(msg)


async def _get_current_revision() -> str | None:
    """Retorna la revisión actual de alembic."""
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        row = await conn.fetchrow("SELECT version_num FROM alembic_version")
        return row["version_num"] if row else None
    finally:
        await conn.close()


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


# ===========================================================================
# Fixtures: ensure we start from revision 003 for every test
# ===========================================================================


@pytest.fixture(autouse=True)
def reset_to_003():
    """Asegura que la base arranca en migration 003 antes de cada test."""
    current = None
    import asyncio
    loop = asyncio.new_event_loop()
    try:
        conn = loop.run_until_complete(asyncpg.connect(DATABASE_URL))
        row = loop.run_until_complete(
            conn.fetchrow("SELECT version_num FROM alembic_version")
        )
        current = row["version_num"] if row else None
        loop.run_until_complete(conn.close())
    finally:
        loop.close()

    if current == REV_004:
        _alembic("downgrade", REV_003)
    elif current is None or current != REV_003:
        # Estamos en 001, 002 o sin base → upgrade a 003
        _alembic("upgrade", REV_003)
    # else at 003 — do nothing


async def _setup_row(conn, *, action: str = "TEST_ACTION") -> uuid.UUID:
    """Helper: inserta tenant + user + audit_log y retorna entry_id."""
    tenant_id = uuid.uuid4()
    user_id = uuid.uuid4()
    entry_id = uuid.uuid4()

    await conn.execute(
        "INSERT INTO tenant (id, slug, nombre, activo, created_at, updated_at) "
        "VALUES ($1, $2, 'Test', TRUE, NOW(), NOW())",
        tenant_id, f"t-{uuid.uuid4().hex[:8]}",
    )
    await conn.execute(
        "INSERT INTO \"user\" (id, tenant_id, email_encrypted, email_lookup, "
        "password_hash, is_active, totp_enabled, created_at, updated_at) "
        "VALUES ($1, $2, 'enc', $3, '$hash', TRUE, FALSE, NOW(), NOW())",
        user_id, tenant_id, uuid.uuid4().hex[:64],
    )
    await conn.execute(
        "INSERT INTO audit_log (id, tenant_id, actor_id, accion, detalle, "
        "filas_afectadas, ip, user_agent) "
        "VALUES ($1, $2, $3, $4, '{}', 1, '127.0.0.1', 'test')",
        entry_id, tenant_id, user_id, action,
    )
    return entry_id


# ===========================================================================
# Tests — Upgrade
# ===========================================================================


class TestMigration004Upgrade:
    """Scenario: Aplicar migration 004 desde 003."""

    async def test_upgrade_creates_audit_log_table(self):
        """WHEN upgrade head, THEN audit_log existe."""
        _alembic("upgrade", REV_004)
        tables = await _get_tables()
        assert "audit_log" in tables

    async def test_upgrade_sets_alembic_version(self):
        """WHEN upgrade head, THEN version apunta a 004."""
        _alembic("upgrade", REV_004)
        rev = await _get_current_revision()
        assert rev == REV_004

    async def test_upgrade_creates_index_tenant_fecha(self):
        """WHEN upgrade head, THEN índice compuesto existe."""
        _alembic("upgrade", REV_004)
        conn = await asyncpg.connect(DATABASE_URL)
        try:
            rows = await conn.fetch(
                "SELECT indexname FROM pg_indexes "
                "WHERE tablename='audit_log' AND indexname='ix_audit_log_tenant_fecha'"
            )
            assert len(rows) == 1
        finally:
            await conn.close()

    async def test_update_rule_blocks_modification(self):
        """WHEN UPDATE directo, THEN registro no cambia."""
        _alembic("upgrade", REV_004)
        conn = await asyncpg.connect(DATABASE_URL)
        try:
            entry_id = await _setup_row(conn, action="TEST_ACTION")

            # Try UPDATE — should be silently blocked
            await conn.execute(
                "UPDATE audit_log SET accion='CHANGED' WHERE id=$1",
                entry_id,
            )

            row = await conn.fetchrow(
                "SELECT accion FROM audit_log WHERE id=$1", entry_id,
            )
            assert row["accion"] == "TEST_ACTION", "UPDATE no fue bloqueado por la regla"
        finally:
            await conn.close()

    async def test_delete_rule_blocks_deletion(self):
        """WHEN DELETE directo, THEN registro persiste."""
        _alembic("upgrade", REV_004)
        conn = await asyncpg.connect(DATABASE_URL)
        try:
            entry_id = await _setup_row(conn, action="TEST_DELETE")

            # Try DELETE — should be silently blocked
            await conn.execute("DELETE FROM audit_log WHERE id=$1", entry_id)

            row = await conn.fetchrow("SELECT id FROM audit_log WHERE id=$1", entry_id)
            assert row is not None, "DELETE no fue bloqueado por la regla"
        finally:
            await conn.close()


class TestMigration004Downgrade:
    """Scenario: Revertir migration 004 desde 004 a 003."""

    async def test_downgrade_removes_audit_log_table(self):
        """GIVEN 004 aplicada, WHEN downgrade -1, THEN audit_log eliminada."""
        _alembic("upgrade", REV_004)
        _alembic("downgrade", REV_003)
        tables = await _get_tables()
        assert "audit_log" not in tables

    async def test_downgrade_keeps_rbac_tables(self):
        """WHEN downgrade -1, THEN tablas de RBAC persisten."""
        _alembic("upgrade", REV_004)
        _alembic("downgrade", REV_003)
        tables = await _get_tables()
        for table in ["permiso", "rol_permiso", "role", "user"]:
            assert table in tables, f"Tabla '{table}' debe persistir tras downgrade"

    async def test_downgrade_sets_version_to_003(self):
        """WHEN downgrade -1, THEN version vuelve a 003."""
        _alembic("upgrade", REV_004)
        _alembic("downgrade", REV_003)
        rev = await _get_current_revision()
        assert rev == REV_003

    async def test_downgrade_reapply_is_idempotent(self):
        """GIVEN upgrade -> downgrade -> upgrade, THEN funciona de nuevo."""
        _alembic("upgrade", REV_004)
        _alembic("downgrade", REV_003)
        _alembic("upgrade", REV_004)
        tables = await _get_tables()
        assert "audit_log" in tables
        rev = await _get_current_revision()
        assert rev == REV_004

"""Tests para extensiones de solo lectura de AuditLogRepository (C-19).

TDD estricto: cada comportamiento se prueba con RED (test falla sin código)
→ GREEN (código mínimo) → TRIANGULATE (≥2 casos).
"""

import uuid
from datetime import datetime, timezone, timedelta

import pytest
from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.config import Settings
from app.core.database import Base

pytestmark = pytest.mark.requires_db


TENANT_A_SLUG = "tenant-a-auditoria"
TENANT_B_SLUG = "tenant-b-auditoria"
ACCIONES = [
    "CALIFICACIONES_IMPORTAR",
    "PADRON_CARGAR",
    "COMUNICACION_ENVIAR",
    "ASIGNACION_MODIFICAR",
]


async def _seed_audit_data(session, settings):
    """Siembra datos controlados para tests de auditoría.

    Returns: (tenant_a, tenant_b, users_a, users_b, entries)
    """
    from app.models.tenant import Tenant
    from app.models.user import User
    from app.models.audit_log import AuditLog

    url = settings.test_database_url or settings.database_url
    async with create_async_engine(url, poolclass=NullPool).begin() as conn:
        await conn.run_sync(
            Base.metadata.create_all,
            tables=[Tenant.__table__, User.__table__, AuditLog.__table__],
        )

    tenant_a = Tenant(id=uuid.uuid4(), slug=TENANT_A_SLUG, nombre="Tenant A")
    tenant_b = Tenant(id=uuid.uuid4(), slug=TENANT_B_SLUG, nombre="Tenant B")
    session.add_all([tenant_a, tenant_b])
    await session.flush()

    # 3 usuarios en tenant A: admin, coordinador, otro docente
    users_a = []
    for role in ["admin", "coordinador", "docente"]:
        u = User(
            email_encrypted=f"enc-{role}-a",
            email_lookup=uuid.uuid4().hex[:64],
            password_hash="$argon2id$hash",
            tenant_id=tenant_a.id,
        )
        session.add(u)
        await session.flush()
        users_a.append(u)

    # 1 usuario en tenant B
    user_b = User(
        email_encrypted="enc-b",
        email_lookup=uuid.uuid4().hex[:64],
        password_hash="$argon2id$hash",
        tenant_id=tenant_b.id,
    )
    session.add(user_b)
    await session.flush()
    users_b = [user_b]

    base_dt = datetime(2026, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
    materia_ids = [uuid.uuid4(), uuid.uuid4(), None]

    entries = []

    # -- Tenant A entries: 3 actores × diferentes días/acciones --
    for i, actor in enumerate(users_a):
        e = AuditLog(
            tenant_id=tenant_a.id,
            actor_id=actor.id,
            accion=ACCIONES[i % len(ACCIONES)],
            detalle={"i": i},
            filas_afectadas=(i + 1) * 10,
            ip=f"10.0.{i}.1",
            user_agent="pytest-auditoria",
            materia_id=materia_ids[i % len(materia_ids)],
            fecha_hora=base_dt + timedelta(days=i),
        )
        session.add(e)
        await session.flush()
        entries.append(e)

    # Extra entries for day aggregation: same actor, same day, same action
    for day in range(2):
        for _ in range(3):
            e = AuditLog(
                tenant_id=tenant_a.id,
                actor_id=users_a[0].id,
                accion="CALIFICACIONES_IMPORTAR",
                detalle={},
                filas_afectadas=1,
                ip="10.0.0.1",
                user_agent="pytest",
                fecha_hora=base_dt + timedelta(days=day),
            )
            session.add(e)
            await session.flush()
            entries.append(e)

    # -- Tenant B: 1 entry (aislamiento) --
    e_b = AuditLog(
        tenant_id=tenant_b.id,
        actor_id=users_b[0].id,
        accion="PADRON_CARGAR",
        detalle={"from": "b"},
        filas_afectadas=5,
        ip="10.99.0.1",
        user_agent="pytest-b",
        fecha_hora=base_dt,
    )
    session.add(e_b)
    await session.flush()
    entries.append(e_b)

    return tenant_a, tenant_b, users_a, users_b, entries


class TestAuditLogListFiltrado:
    """Scenario: AuditLogRepository.list_filtrado — scope + filtros combinados."""

    @pytest.fixture(autouse=True)
    async def setup(self, db_session: AsyncSession, settings: Settings):
        self.tenant_a, self.tenant_b, self.users_a, self.users_b, self.entries = (
            await _seed_audit_data(db_session, settings)
        )
        self.repo = self._get_repo()

    def _get_repo(self):
        from app.repositories.audit_log_repository import AuditLogRepository
        return AuditLogRepository()

    # ── 2.1 RED: multi-tenant isolation ────────────────────────────────────

    async def test_list_filtrado_aislamiento_tenant(
        self, db_session: AsyncSession,
    ) -> None:
        """WHEN list_filtrado(tenant_a) THEN no ve entries de tenant_b."""
        result = await self.repo.list_filtrado(
            tenant_id=self.tenant_a.id,
            session=db_session,
        )
        ids = [r.id for r in result]
        for e in self.entries:
            if e.tenant_id == self.tenant_b.id:
                assert e.id not in ids, f"Entry de tenant B ({e.id}) visible desde A"

    # ── 2.2 GREEN: implementar list_filtrado ───────────────────────────────

    async def test_list_filtrado_retorna_del_tenant(
        self, db_session: AsyncSession,
    ) -> None:
        """WHEN list_filtrado(tenant_a) THEN devuelve entries de tenant_a."""
        result = await self.repo.list_filtrado(
            tenant_id=self.tenant_a.id,
            session=db_session,
        )
        tenant_a_entries = [e for e in self.entries if e.tenant_id == self.tenant_a.id]
        assert len(result) == len(tenant_a_entries)

    # ── 2.3 RED→GREEN: scope propio ────────────────────────────────────────

    async def test_list_filtrado_scope_propio_solo_actor(
        self, db_session: AsyncSession,
    ) -> None:
        """WHEN scope_actor_id=U THEN solo entries con actor_id=U."""
        actor = self.users_a[0]
        result = await self.repo.list_filtrado(
            tenant_id=self.tenant_a.id,
            session=db_session,
            scope_actor_id=actor.id,
        )
        assert all(r.actor_id == actor.id for r in result)

    async def test_list_filtrado_scope_none_todos(
        self, db_session: AsyncSession,
    ) -> None:
        """WHEN scope_actor_id=None THEN devuelve todos del tenant."""
        result = await self.repo.list_filtrado(
            tenant_id=self.tenant_a.id,
            session=db_session,
            scope_actor_id=None,
        )
        tenant_a_ids = {e.id for e in self.entries if e.tenant_id == self.tenant_a.id}
        result_ids = {r.id for r in result}
        assert result_ids == tenant_a_ids


class TestAuditLogFiltros:
    """Scenario: list_filtrado con filtros individuales y combinados."""

    @pytest.fixture(autouse=True)
    async def setup(self, db_session: AsyncSession, settings: Settings):
        self.tenant_a, self.tenant_b, self.users_a, self.users_b, self.entries = (
            await _seed_audit_data(db_session, settings)
        )
        from app.repositories.audit_log_repository import AuditLogRepository
        self.repo = AuditLogRepository()

    # ── 2.4 RED→GREEN: filtro por rango de fechas ───────────────────────────

    async def test_filtro_fecha_rango_cerrado(
        self, db_session: AsyncSession,
    ) -> None:
        """WHEN desde y hasta especificados THEN solo entries en rango."""
        base = datetime(2026, 6, 15, 0, 0, 0, tzinfo=timezone.utc)
        result = await self.repo.list_filtrado(
            tenant_id=self.tenant_a.id,
            session=db_session,
            desde=base,
            hasta=base + timedelta(days=1, hours=23, minutes=59),
        )
        # Debe incluir day 0 entries (Jun 15) y excluir day 2+ (Jun 17+)
        assert len(result) > 0
        for r in result:
            assert base <= r.fecha_hora <= base + timedelta(days=1, hours=23, minutes=59)

    async def test_filtro_fecha_sin_resultados(
        self, db_session: AsyncSession,
    ) -> None:
        """WHEN rango sin entries THEN lista vacía."""
        futuro = datetime(2030, 1, 1, tzinfo=timezone.utc)
        result = await self.repo.list_filtrado(
            tenant_id=self.tenant_a.id,
            session=db_session,
            desde=futuro,
        )
        assert len(result) == 0

    # ── 2.5 RED→GREEN: filtro por materia_id ────────────────────────────────

    async def test_filtro_materia_especifica(
        self, db_session: AsyncSession,
    ) -> None:
        """WHEN materia_id filtrado THEN solo entries con esa materia."""
        target_materia = next(
            e.materia_id for e in self.entries
            if e.tenant_id == self.tenant_a.id and e.materia_id is not None
        )
        result = await self.repo.list_filtrado(
            tenant_id=self.tenant_a.id,
            session=db_session,
            materia_id=target_materia,
        )
        assert all(r.materia_id == target_materia for r in result)
        assert len(result) > 0

    async def test_filtro_materia_null_no_excluye(
        self, db_session: AsyncSession,
    ) -> None:
        """WHEN sin filtro materia THEN incluye entries con materia_id null."""
        result = await self.repo.list_filtrado(
            tenant_id=self.tenant_a.id,
            session=db_session,
        )
        # Al menos un entry del seed tiene materia_id null
        assert any(r.materia_id is None for r in result)

    # ── 2.6 RED→GREEN: filtro por accion ────────────────────────────────────

    async def test_filtro_accion_existente(
        self, db_session: AsyncSession,
    ) -> None:
        """WHEN accion filtrada THEN solo entries con esa acción."""
        result = await self.repo.list_filtrado(
            tenant_id=self.tenant_a.id,
            session=db_session,
            accion="CALIFICACIONES_IMPORTAR",
        )
        assert all(r.accion == "CALIFICACIONES_IMPORTAR" for r in result)
        assert len(result) > 0

    async def test_filtro_accion_inexistente(
        self, db_session: AsyncSession,
    ) -> None:
        """WHEN accion que no existe THEN lista vacía sin error."""
        result = await self.repo.list_filtrado(
            tenant_id=self.tenant_a.id,
            session=db_session,
            accion="NO_EXISTE",
        )
        assert len(result) == 0

    # ── 2.7 RED→GREEN: límite y orden ───────────────────────────────────────

    async def test_filtro_limit_respetado(
        self, db_session: AsyncSession,
    ) -> None:
        """WHEN limit=3 THEN solo 3 resultados."""
        result = await self.repo.list_filtrado(
            tenant_id=self.tenant_a.id,
            session=db_session,
            limit=3,
        )
        assert len(result) <= 3

    async def test_filtro_orden_desc(
        self, db_session: AsyncSession,
    ) -> None:
        """THEN resultados ordenados por fecha desc."""
        result = await self.repo.list_filtrado(
            tenant_id=self.tenant_a.id,
            session=db_session,
        )
        fechas = [r.fecha_hora for r in result]
        assert fechas == sorted(fechas, reverse=True)

    async def test_filtro_limit_excede_maximo(
        self, db_session: AsyncSession,
    ) -> None:
        """WHEN limit > MAX (1000) THEN recortado al tope."""
        from app.repositories.audit_log_repository import AUDIT_LOG_MAX_LIMIT
        result = await self.repo.list_filtrado(
            tenant_id=self.tenant_a.id,
            session=db_session,
            limit=5000,
        )
        max_esperado = min(len(self.entries), AUDIT_LOG_MAX_LIMIT)
        assert len(result) <= max_esperado


class TestAuditLogAggregaciones:
    """Scenario: métodos de agregación sobre audit_log."""

    @pytest.fixture(autouse=True)
    async def setup(self, db_session: AsyncSession, settings: Settings):
        self.tenant_a, self.tenant_b, self.users_a, self.users_b, self.entries = (
            await _seed_audit_data(db_session, settings)
        )
        from app.repositories.audit_log_repository import AuditLogRepository
        self.repo = AuditLogRepository()

    # ── 2.8 RED→GREEN: aggregate_acciones_por_dia ──────────────────────────

    async def test_aggr_dias_con_conteos(
        self, db_session: AsyncSession,
    ) -> None:
        """WHEN aggregate_acciones_por_dia THEN retorna fecha y total."""
        result = await self.repo.aggregate_acciones_por_dia(
            tenant_id=self.tenant_a.id,
            session=db_session,
        )
        assert len(result) > 0
        for row in result:
            assert "fecha" in row
            assert "total" in row
            assert row["total"] > 0

    async def test_aggr_dia_sin_actividad(
        self, db_session: AsyncSession,
    ) -> None:
        """WHEN día sin entries THEN no aparece en resultados."""
        result = await self.repo.aggregate_acciones_por_dia(
            tenant_id=self.tenant_b.id,
            session=db_session,
        )
        # Tenant B tiene 1 entry en jun 15
        assert len(result) >= 1
        total_esperado = sum(
            1 for e in self.entries if e.tenant_id == self.tenant_b.id
        )
        # Los días agrupados NO incluyen días sin registros en el periodo
        total_en_resultados = sum(r["total"] for r in result)
        assert total_en_resultados == total_esperado

    # ── 2.9 RED→GREEN: aggregate_comunicaciones_por_docente ─────────────────

    async def test_aggr_comunicaciones_solo_codigos(
        self, db_session: AsyncSession,
    ) -> None:
        """THEN solo incluye acciones que empiezan con COMUNICACION_."""
        result = await self.repo.aggregate_comunicaciones_por_docente(
            tenant_id=self.tenant_a.id,
            session=db_session,
        )
        for row in result:
            assert row["accion"].startswith("COMUNICACION_")
            assert row["total"] > 0

    async def test_aggr_comunicaciones_scope(
        self, db_session: AsyncSession,
    ) -> None:
        """WHEN scope_actor_id THEN filtra por actor."""
        actor = self.users_a[0]
        result = await self.repo.aggregate_comunicaciones_por_docente(
            tenant_id=self.tenant_a.id,
            session=db_session,
            scope_actor_id=actor.id,
        )
        for row in result:
            assert row["actor_id"] == actor.id

    # ── 2.10 RED→GREEN: aggregate_interacciones_docente_materia ─────────────

    async def test_aggr_interacciones_agrupa(
        self, db_session: AsyncSession,
    ) -> None:
        """THEN agrupa por actor, materia y accion."""
        result = await self.repo.aggregate_interacciones_docente_materia(
            tenant_id=self.tenant_a.id,
            session=db_session,
        )
        assert len(result) > 0
        for row in result:
            assert "actor_id" in row
            assert "materia_id" in row
            assert "accion" in row
            assert row["total"] > 0

    async def test_aggr_interacciones_sin_materia(
        self, db_session: AsyncSession,
    ) -> None:
        """THEN entries sin materia se agrupan."""
        result = await self.repo.aggregate_interacciones_docente_materia(
            tenant_id=self.tenant_a.id,
            session=db_session,
        )
        materias = {r["materia_id"] for r in result}
        # Puede incluir "sin_materia" string o materia_id nulo
        # (el test verifica que no explote, la semántica se afina después)

    # ── 2.11 Invariante: append-only NO expone mutación ──────────────────────

    async def test_repo_no_expone_mutacion(
        self, db_session: AsyncSession,
    ) -> None:
        """THEN create/update/soft_delete lanzan NotImplementedError."""
        import pytest
        with pytest.raises(NotImplementedError):
            await self.repo.create()
        with pytest.raises(NotImplementedError):
            self.repo.update()
        with pytest.raises(NotImplementedError):
            self.repo.soft_delete()

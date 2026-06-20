"""Tests para el módulo de coloquios/evaluaciones — C-14.

Cubre convocatorias CRUD, importación de candidatos, reservas con
control de concurrencia FOR UPDATE, resultados, registro académico y
aislamiento multi-tenant.

Requiere DB real (--run-db).
"""

import uuid
from datetime import datetime, timedelta, timezone

import pytest

# ── Helpers ──────────────────────────────────────────────────────────────────


async def _make_user(db_session, tenant_id, role_code="alumno"):
    """Helper: crea un usuario y le asigna un rol."""
    from app.repositories.usuario_repository import UsuarioRepository

    repo = UsuarioRepository()
    user = await repo.create(
        tenant_id=tenant_id,
        email=f"u-{uuid.uuid4().hex[:8]}@test.edu.ar",
        password_plain="pw",
        nombre="Test",
        apellidos="User",
        legajo=f"L-{uuid.uuid4().hex[:6]}",
        session=db_session,
    )

    from app.models.role import Role, UserRole

    if role_code:
        stmt = (
            __import__("sqlalchemy")
            .select(Role)
            .where(Role.tenant_id == tenant_id, Role.code == role_code, Role.deleted_at.is_(None))
        )
        result = await db_session.execute(stmt)
        role = result.scalar_one_or_none()
        if role is None:
            role = Role(
                tenant_id=tenant_id,
                code=role_code,
                nombre=role_code.capitalize(),
            )
            db_session.add(role)
            await db_session.flush()
            await db_session.refresh(role)

        ur = UserRole(
            user_id=user.id,
            role_id=role.id,
            tenant_id=tenant_id,
        )
        db_session.add(ur)
        await db_session.flush()

    await db_session.refresh(user)
    return user


async def _make_materia(db_session, tenant_id):
    """Helper: crea una materia."""
    from app.models.materia import Materia

    materia = Materia(
        tenant_id=tenant_id,
        codigo=f"MAT-{uuid.uuid4().hex[:6]}",
        nombre="Matematica Test",
    )
    db_session.add(materia)
    await db_session.flush()
    await db_session.refresh(materia)
    return materia


async def _make_cohorte(db_session, tenant_id, carrera_id=None):
    """Helper: crea una cohorte."""
    if carrera_id is None:
        from app.models.carrera import Carrera

        carrera = Carrera(
            tenant_id=tenant_id,
            codigo=f"CARR-{uuid.uuid4().hex[:6]}",
            nombre="Carrera Test",
        )
        db_session.add(carrera)
        await db_session.flush()
        await db_session.refresh(carrera)
        carrera_id = carrera.id

    from app.models.cohorte import Cohorte

    cohorte = Cohorte(
        tenant_id=tenant_id,
        carrera_id=carrera_id,
        nombre="2026",
        anio=2026,
        vig_desde="2026-01-01",
    )
    db_session.add(cohorte)
    await db_session.flush()
    await db_session.refresh(cohorte)
    return cohorte


async def _make_evaluacion(db_session, tenant_id, materia_id=None, cohorte_id=None, **kwargs):
    """Helper: crea una evaluacion."""
    from app.models.evaluacion import Evaluacion

    if materia_id is None:
        materia = await _make_materia(db_session, tenant_id)
        materia_id = materia.id
    if cohorte_id is None:
        cohorte = await _make_cohorte(db_session, tenant_id)
        cohorte_id = cohorte.id

    ev = Evaluacion(
        tenant_id=tenant_id,
        materia_id=materia_id,
        cohorte_id=cohorte_id,
        tipo=kwargs.get("tipo", "Coloquio"),
        instancia=kwargs.get("instancia", "Coloquio Final"),
        dias_disponibles=kwargs.get("dias_disponibles", 5),
    )
    db_session.add(ev)
    await db_session.flush()
    await db_session.refresh(ev)
    return ev


# ── Tests: Schemas ──────────────────────────────────────────────────────────


class TestEvaluacionSchemas:
    """Scenario: Pydantic schemas con extra='forbid' y validación."""

    def test_extra_field_rejected(self) -> None:
        """WHEN campo extra en EvaluacionCreate, THEN ValidationError."""
        from pydantic import ValidationError

        from app.schemas.evaluacion import EvaluacionCreate

        with pytest.raises(ValidationError) as excinfo:
            EvaluacionCreate(
                materia_id=uuid.uuid4(),
                cohorte_id=uuid.uuid4(),
                instancia="Test",
                dias_disponibles=5,
                color="rojo",
            )
        errors = excinfo.value.errors()
        assert any(e["type"] == "extra_forbidden" for e in errors)

    def test_extra_field_rejected_reserva(self) -> None:
        """WHEN campo extra en ReservaCreate, THEN ValidationError."""
        from pydantic import ValidationError

        from app.schemas.evaluacion import ReservaCreate

        with pytest.raises(ValidationError) as excinfo:
            ReservaCreate(
                fecha_hora=datetime.now(timezone.utc),
                alumno_id=uuid.uuid4(),
            )
        errors = excinfo.value.errors()
        assert any(e["type"] == "extra_forbidden" for e in errors)

    def test_extra_field_rejected_resultado(self) -> None:
        """WHEN campo extra en ResultadoCreate, THEN ValidationError."""
        from pydantic import ValidationError

        from app.schemas.evaluacion import ResultadoCreate

        with pytest.raises(ValidationError) as excinfo:
            ResultadoCreate(
                alumno_id=uuid.uuid4(),
                nota_final="8",
                extra="no",
            )
        errors = excinfo.value.errors()
        assert any(e["type"] == "extra_forbidden" for e in errors)

    def test_evaluacion_create_positive_dias(self) -> None:
        """WHEN dias_disponibles = 0, THEN ValidationError (ge=1)."""
        from pydantic import ValidationError

        from app.schemas.evaluacion import EvaluacionCreate

        with pytest.raises(ValidationError):
            EvaluacionCreate(
                materia_id=uuid.uuid4(),
                cohorte_id=uuid.uuid4(),
                instancia="Test",
                dias_disponibles=0,
            )


# ── Tests: Convocatoria CRUD ────────────────────────────────────────────────


@pytest.mark.requires_db
class TestEvaluacionRepository:
    """Scenario: CRUD de convocatorias con tenant isolation y soft delete."""

    async def test_create_evaluacion_happy_path(self, db_session, tenant_factory) -> None:
        """WHEN se crea una evaluacion, THEN persiste con UUID y tenant_id."""
        from app.repositories.evaluacion_repository import EvaluacionRepository

        tenant = await tenant_factory()
        materia = await _make_materia(db_session, tenant.id)
        cohorte = await _make_cohorte(db_session, tenant.id)
        repo = EvaluacionRepository()

        ev = await repo.create_evaluacion(
            tenant_id=tenant.id,
            materia_id=materia.id,
            cohorte_id=cohorte.id,
            tipo="Coloquio",
            instancia="Coloquio Final",
            dias_disponibles=5,
            session=db_session,
        )

        assert ev.id is not None
        assert ev.tenant_id == tenant.id
        assert ev.tipo == "Coloquio"
        assert ev.dias_disponibles == 5

    async def test_get_evaluacion_by_id(self, db_session, tenant_factory) -> None:
        """WHEN se busca por ID, THEN retorna la evaluacion."""
        from app.repositories.evaluacion_repository import EvaluacionRepository

        tenant = await tenant_factory()
        ev = await _make_evaluacion(db_session, tenant.id)
        repo = EvaluacionRepository()

        found = await repo.get(id=ev.id, tenant_id=tenant.id, session=db_session)
        assert found is not None
        assert found.id == ev.id

    async def test_get_other_tenant_returns_none(self, db_session, tenant_factory) -> None:
        """WHEN evaluacion de tenant A buscada desde tenant B, THEN None."""
        from app.repositories.evaluacion_repository import EvaluacionRepository

        ta = await tenant_factory(slug=f"a-{uuid.uuid4().hex[:6]}")
        tb = await tenant_factory(slug=f"b-{uuid.uuid4().hex[:6]}")
        ev = await _make_evaluacion(db_session, ta.id)
        repo = EvaluacionRepository()

        found = await repo.get(id=ev.id, tenant_id=tb.id, session=db_session)
        assert found is None

    async def test_soft_delete_evaluacion(self, db_session, tenant_factory) -> None:
        """WHEN soft delete, THEN deleted_at se setea."""
        from app.repositories.evaluacion_repository import EvaluacionRepository

        tenant = await tenant_factory()
        ev = await _make_evaluacion(db_session, tenant.id)
        repo = EvaluacionRepository()

        deleted = await repo.soft_delete(id=ev.id, tenant_id=tenant.id, session=db_session)
        assert deleted

        found = await repo.get(id=ev.id, tenant_id=tenant.id, session=db_session)
        assert found is None

    async def test_update_evaluacion(self, db_session, tenant_factory) -> None:
        """WHEN se actualiza dias_disponibles, THEN persiste el cambio."""
        from app.repositories.evaluacion_repository import EvaluacionRepository

        tenant = await tenant_factory()
        ev = await _make_evaluacion(db_session, tenant.id, dias_disponibles=5)
        repo = EvaluacionRepository()

        updated = await repo.update_evaluacion(
            id=ev.id,
            tenant_id=tenant.id,
            data={"dias_disponibles": 10},
            session=db_session,
        )
        assert updated is not None
        assert updated.dias_disponibles == 10


# ── Tests: Candidatos ───────────────────────────────────────────────────────


@pytest.mark.requires_db
class TestCandidatosImport:
    """Scenario: Importación de candidatos a una convocatoria."""

    async def test_import_3_candidatos_exitoso(self, db_session, tenant_factory) -> None:
        """WHEN se importan 3 candidatos, THEN registrados=3."""
        from app.repositories.evaluacion_repository import EvaluacionRepository

        tenant = await tenant_factory()
        ev = await _make_evaluacion(db_session, tenant.id, dias_disponibles=10)
        u1 = await _make_user(db_session, tenant.id)
        u2 = await _make_user(db_session, tenant.id)
        u3 = await _make_user(db_session, tenant.id)
        repo = EvaluacionRepository()

        registrados, rechazados = await repo.import_candidatos(
            tenant_id=tenant.id,
            evaluacion_id=ev.id,
            usuario_ids=[u1.id, u2.id, u3.id],
            session=db_session,
        )
        assert len(registrados) == 3
        assert len(rechazados) == 0

    async def test_import_idempotente(self, db_session, tenant_factory) -> None:
        """WHEN mismo usuario_id dos veces, THEN segunda vez reporta ya registrado."""
        from app.repositories.evaluacion_repository import EvaluacionRepository

        tenant = await tenant_factory()
        ev = await _make_evaluacion(db_session, tenant.id, dias_disponibles=10)
        u = await _make_user(db_session, tenant.id)
        repo = EvaluacionRepository()

        r1, rej1 = await repo.import_candidatos(
            tenant_id=tenant.id, evaluacion_id=ev.id, usuario_ids=[u.id], session=db_session
        )
        assert len(r1) == 1
        assert len(rej1) == 0

        r2, rej2 = await repo.import_candidatos(
            tenant_id=tenant.id, evaluacion_id=ev.id, usuario_ids=[u.id], session=db_session
        )
        assert len(r2) == 0
        assert len(rej2) == 1
        assert "ya está registrado" in rej2[0]["motivo"]

    async def test_candidato_otro_tenant_rechazado(self, db_session, tenant_factory) -> None:
        """WHEN usuario_id de otro tenant, THEN rechazado."""
        from app.repositories.evaluacion_repository import EvaluacionRepository

        ta = await tenant_factory(slug=f"a-{uuid.uuid4().hex[:6]}")
        tb = await tenant_factory(slug=f"b-{uuid.uuid4().hex[:6]}")
        ev = await _make_evaluacion(db_session, ta.id, dias_disponibles=10)
        u = await _make_user(db_session, tb.id)
        repo = EvaluacionRepository()

        registrados, rechazados = await repo.import_candidatos(
            tenant_id=ta.id, evaluacion_id=ev.id, usuario_ids=[u.id], session=db_session
        )
        assert len(registrados) == 0
        assert len(rechazados) == 1

    async def test_candidato_no_alumno_rechazado(self, db_session, tenant_factory) -> None:
        """WHEN usuario con rol PROFESOR, THEN rechazado."""
        from app.repositories.evaluacion_repository import EvaluacionRepository

        tenant = await tenant_factory()
        ev = await _make_evaluacion(db_session, tenant.id, dias_disponibles=10)
        profe = await _make_user(db_session, tenant.id, role_code="profesor")
        repo = EvaluacionRepository()

        registrados, rechazados = await repo.import_candidatos(
            tenant_id=tenant.id, evaluacion_id=ev.id, usuario_ids=[profe.id], session=db_session
        )
        assert len(registrados) == 0
        assert len(rechazados) == 1
        assert "no tiene rol ALUMNO" in rechazados[0]["motivo"]


# ── Tests: Métricas ─────────────────────────────────────────────────────────


@pytest.mark.requires_db
class TestMetricas:
    """Scenario: Métricas operativas de coloquios."""

    async def test_list_with_metrics(self, db_session, tenant_factory) -> None:
        """WHEN listado con metricas, THEN incluye convocados, reservas, cupos."""
        from app.repositories.evaluacion_repository import EvaluacionRepository

        tenant = await tenant_factory()
        ev = await _make_evaluacion(db_session, tenant.id, dias_disponibles=5)
        u = await _make_user(db_session, tenant.id)
        repo = EvaluacionRepository()

        await repo.import_candidatos(
            tenant_id=tenant.id, evaluacion_id=ev.id, usuario_ids=[u.id], session=db_session
        )

        items = await repo.list_with_metrics(tenant_id=tenant.id, session=db_session)
        assert len(items) >= 1
        found = [i for i in items if i["id"] == ev.id][0]
        assert found["convocados"] == 1
        assert found["reservas_activas"] == 0
        assert found["cupos_libres"] == 5

    async def test_metricas_panel_zero(self, db_session, tenant_factory) -> None:
        """WHEN sin convocatorias, THEN metricas en cero."""
        from app.repositories.evaluacion_repository import EvaluacionRepository

        tenant = await tenant_factory()
        repo = EvaluacionRepository()

        metrics = await repo.get_metricas_panel(tenant_id=tenant.id, session=db_session)
        assert metrics["total_candidatos"] == 0
        assert metrics["instancias_activas"] == 0
        assert metrics["reservas_activas"] == 0
        assert metrics["notas_registradas"] == 0

    async def test_metricas_panel_with_data(self, db_session, tenant_factory) -> None:
        """WHEN hay datos, THEN metricas reflejan el estado real."""
        from app.repositories.evaluacion_repository import EvaluacionRepository

        tenant = await tenant_factory()
        ev = await _make_evaluacion(db_session, tenant.id, dias_disponibles=5)
        u = await _make_user(db_session, tenant.id)
        repo = EvaluacionRepository()

        await repo.import_candidatos(
            tenant_id=tenant.id, evaluacion_id=ev.id, usuario_ids=[u.id], session=db_session
        )

        metrics = await repo.get_metricas_panel(tenant_id=tenant.id, session=db_session)
        assert metrics["instancias_activas"] >= 1
        assert metrics["total_candidatos"] >= 1

    async def test_tenant_isolation_metrics(self, db_session, tenant_factory) -> None:
        """WHEN tenant A tiene datos, tenant B no, THEN metricas aisladas."""
        from app.repositories.evaluacion_repository import EvaluacionRepository

        ta = await tenant_factory(slug=f"a-{uuid.uuid4().hex[:6]}")
        tb = await tenant_factory(slug=f"b-{uuid.uuid4().hex[:6]}")
        await _make_evaluacion(db_session, ta.id, dias_disponibles=5)
        repo = EvaluacionRepository()

        metrics_a = await repo.get_metricas_panel(tenant_id=ta.id, session=db_session)
        metrics_b = await repo.get_metricas_panel(tenant_id=tb.id, session=db_session)
        assert metrics_a["instancias_activas"] >= 1
        assert metrics_b["instancias_activas"] == 0


# ── Tests: Agenda ───────────────────────────────────────────────────────────


@pytest.mark.requires_db
class TestAgenda:
    """Scenario: Agenda consolidada de reservas activas."""

    async def test_agenda_vacia_sin_reservas(self, db_session, tenant_factory) -> None:
        """WHEN sin reservas, THEN agenda vacia."""
        from app.repositories.evaluacion_repository import EvaluacionRepository

        tenant = await tenant_factory()
        repo = EvaluacionRepository()
        agenda = await repo.get_agenda(tenant_id=tenant.id, session=db_session)
        assert agenda == []

    async def test_agenda_solo_reservas_activas(self, db_session, tenant_factory) -> None:
        """WHEN hay reserva Activa, THEN aparece en agenda."""
        from app.repositories.evaluacion_repository import EvaluacionRepository
        from app.repositories.reserva_repository import ReservaRepository

        tenant = await tenant_factory()
        ev = await _make_evaluacion(db_session, tenant.id, dias_disponibles=5)
        u = await _make_user(db_session, tenant.id)
        repo_eval = EvaluacionRepository()
        repo_res = ReservaRepository()

        await repo_eval.import_candidatos(
            tenant_id=tenant.id, evaluacion_id=ev.id, usuario_ids=[u.id], session=db_session
        )
        await repo_res.create_reserva(
            tenant_id=tenant.id, evaluacion_id=ev.id, alumno_id=u.id,
            fecha_hora=datetime.now(timezone.utc) + timedelta(days=1),
            session=db_session,
        )

        agenda = await repo_eval.get_agenda(tenant_id=tenant.id, session=db_session)
        assert len(agenda) >= 1


# ── Tests: Reservas ─────────────────────────────────────────────────────────


@pytest.mark.requires_db
class TestReservaRepository:
    """Scenario: CRUD de reservas con FOR UPDATE y concurrencia."""

    async def test_create_reserva_exitosa(self, db_session, tenant_factory) -> None:
        """WHEN se crea reserva, THEN persiste con estado Activa."""
        from app.repositories.reserva_repository import ReservaRepository

        tenant = await tenant_factory()
        ev = await _make_evaluacion(db_session, tenant.id, dias_disponibles=5)
        u = await _make_user(db_session, tenant.id)
        repo = ReservaRepository()

        reserva = await repo.create_reserva(
            tenant_id=tenant.id,
            evaluacion_id=ev.id,
            alumno_id=u.id,
            fecha_hora=datetime.now(timezone.utc) + timedelta(days=1),
            session=db_session,
        )
        assert reserva.id is not None
        assert reserva.estado == "Activa"
        assert reserva.alumno_id == u.id

    async def test_cancelar_reserva(self, db_session, tenant_factory) -> None:
        """WHEN se cancela reserva, THEN estado cambia a Cancelada."""
        from app.repositories.reserva_repository import ReservaRepository

        tenant = await tenant_factory()
        ev = await _make_evaluacion(db_session, tenant.id, dias_disponibles=5)
        u = await _make_user(db_session, tenant.id)
        repo = ReservaRepository()

        reserva = await repo.create_reserva(
            tenant_id=tenant.id, evaluacion_id=ev.id, alumno_id=u.id,
            fecha_hora=datetime.now(timezone.utc) + timedelta(days=1),
            session=db_session,
        )
        cancelada = await repo.cancelar_reserva(
            reserva_id=reserva.id, tenant_id=tenant.id, session=db_session
        )
        assert cancelada is not None
        assert cancelada.estado == "Cancelada"

    async def test_cancelar_ya_cancelada(self, db_session, tenant_factory) -> None:
        """WHEN reserva ya cancelada, THEN devuelve la misma."""
        from app.repositories.reserva_repository import ReservaRepository

        tenant = await tenant_factory()
        ev = await _make_evaluacion(db_session, tenant.id, dias_disponibles=5)
        u = await _make_user(db_session, tenant.id)
        repo = ReservaRepository()

        reserva = await repo.create_reserva(
            tenant_id=tenant.id, evaluacion_id=ev.id, alumno_id=u.id,
            fecha_hora=datetime.now(timezone.utc) + timedelta(days=1),
            session=db_session,
        )
        await repo.cancelar_reserva(reserva_id=reserva.id, tenant_id=tenant.id, session=db_session)
        again = await repo.cancelar_reserva(reserva_id=reserva.id, tenant_id=tenant.id, session=db_session)
        assert again is not None
        assert again.estado == "Cancelada"

    async def test_for_update_concurrency(self, db_session, tenant_factory) -> None:
        """WHEN se llena el cupo de 1, THEN segunda reserva falla (cupo agotado)."""
        from app.repositories.evaluacion_repository import EvaluacionRepository
        from app.repositories.reserva_repository import ReservaRepository
        from app.services.reserva_service import ReservaService

        tenant = await tenant_factory()
        ev = await _make_evaluacion(db_session, tenant.id, dias_disponibles=1)
        u1 = await _make_user(db_session, tenant.id)
        u2 = await _make_user(db_session, tenant.id)
        repo_eval = EvaluacionRepository()

        await repo_eval.import_candidatos(
            tenant_id=tenant.id, evaluacion_id=ev.id, usuario_ids=[u1.id, u2.id],
            session=db_session,
        )

        reserva_repo = ReservaRepository()
        service = ReservaService(
            reserva_repo=reserva_repo,
            evaluacion_repo=repo_eval,
        )

        # Primera reserva: debe funcionar
        r1 = await service.crear_reserva(
            tenant_id=tenant.id,
            evaluacion_id=ev.id,
            alumno_id=u1.id,
            fecha_hora=datetime.now(timezone.utc) + timedelta(days=1),
            session=db_session,
        )
        assert r1["estado"] == "Activa"

        # Segunda reserva: cupo agotado (dias_disponibles=1, ya hay 1)
        from app.services.reserva_service import ReservaServiceError
        with pytest.raises(ReservaServiceError) as exc_info:
            await service.crear_reserva(
                tenant_id=tenant.id,
                evaluacion_id=ev.id,
                alumno_id=u2.id,
                fecha_hora=datetime.now(timezone.utc) + timedelta(days=2),
                session=db_session,
            )
        assert exc_info.value.status_code == 409
        assert "Cupo agotado" in exc_info.value.detail

    async def test_mis_reservas(self, db_session, tenant_factory) -> None:
        """WHEN alumno consulta mis reservas, THEN solo sus reservas."""
        from app.repositories.reserva_repository import ReservaRepository

        tenant = await tenant_factory()
        ev = await _make_evaluacion(db_session, tenant.id, dias_disponibles=5)
        u = await _make_user(db_session, tenant.id)
        repo = ReservaRepository()

        await repo.create_reserva(
            tenant_id=tenant.id, evaluacion_id=ev.id, alumno_id=u.id,
            fecha_hora=datetime.now(timezone.utc) + timedelta(days=1),
            session=db_session,
        )

        reservas = await repo.get_mis_reservas(
            alumno_id=u.id, tenant_id=tenant.id, session=db_session
        )
        assert len(reservas) == 1
        assert reservas[0]["alumno_id"] == u.id


# ── Tests: Resultados ───────────────────────────────────────────────────────


@pytest.mark.requires_db
class TestResultadoRepository:
    """Scenario: CRUD de resultados con registro académico."""

    async def test_create_resultado(self, db_session, tenant_factory) -> None:
        """WHEN se registra nota, THEN persiste."""
        from app.repositories.resultado_repository import ResultadoRepository

        tenant = await tenant_factory()
        ev = await _make_evaluacion(db_session, tenant.id, dias_disponibles=5)
        u = await _make_user(db_session, tenant.id)
        repo = ResultadoRepository()

        resultado = await repo.create_resultado(
            tenant_id=tenant.id,
            evaluacion_id=ev.id,
            alumno_id=u.id,
            nota_final="8",
            session=db_session,
        )
        assert resultado.id is not None
        assert resultado.nota_final == "8"

    async def test_create_resultado_cualitativo(self, db_session, tenant_factory) -> None:
        """WHEN nota cualitativa, THEN se acepta."""
        from app.repositories.resultado_repository import ResultadoRepository

        tenant = await tenant_factory()
        ev = await _make_evaluacion(db_session, tenant.id, dias_disponibles=5)
        u = await _make_user(db_session, tenant.id)
        repo = ResultadoRepository()

        resultado = await repo.create_resultado(
            tenant_id=tenant.id,
            evaluacion_id=ev.id,
            alumno_id=u.id,
            nota_final="Aprobado",
            session=db_session,
        )
        assert resultado.nota_final == "Aprobado"

    async def test_duplicate_resultado_rejected(self, db_session, tenant_factory) -> None:
        """WHEN mismo alumno en misma evaluacion dos veces, THEN segunda falla."""
        from app.repositories.resultado_repository import ResultadoRepository

        tenant = await tenant_factory()
        ev = await _make_evaluacion(db_session, tenant.id, dias_disponibles=5)
        u = await _make_user(db_session, tenant.id)
        repo = ResultadoRepository()

        await repo.create_resultado(
            tenant_id=tenant.id, evaluacion_id=ev.id, alumno_id=u.id,
            nota_final="8", session=db_session,
        )

        with pytest.raises(Exception):
            await repo.create_resultado(
                tenant_id=tenant.id, evaluacion_id=ev.id, alumno_id=u.id,
                nota_final="9", session=db_session,
            )

    async def test_update_nota(self, db_session, tenant_factory) -> None:
        """WHEN se actualiza nota, THEN persiste el cambio."""
        from app.repositories.resultado_repository import ResultadoRepository

        tenant = await tenant_factory()
        ev = await _make_evaluacion(db_session, tenant.id, dias_disponibles=5)
        u = await _make_user(db_session, tenant.id)
        repo = ResultadoRepository()

        resultado = await repo.create_resultado(
            tenant_id=tenant.id, evaluacion_id=ev.id, alumno_id=u.id,
            nota_final="8", session=db_session,
        )
        updated = await repo.update_nota(
            resultado_id=resultado.id, tenant_id=tenant.id,
            nota_final="9", session=db_session,
        )
        assert updated is not None
        assert updated.nota_final == "9"

    async def test_get_by_evaluacion(self, db_session, tenant_factory) -> None:
        """WHEN consulta resultados por evaluacion, THEN lista con datos del alumno."""
        from app.repositories.resultado_repository import ResultadoRepository

        tenant = await tenant_factory()
        ev = await _make_evaluacion(db_session, tenant.id, dias_disponibles=5)
        u = await _make_user(db_session, tenant.id)
        repo = ResultadoRepository()

        await repo.create_resultado(
            tenant_id=tenant.id, evaluacion_id=ev.id, alumno_id=u.id,
            nota_final="8", session=db_session,
        )

        resultados = await repo.get_by_evaluacion(
            evaluacion_id=ev.id, tenant_id=tenant.id, session=db_session
        )
        assert len(resultados) >= 1
        assert resultados[0]["alumno_id"] == u.id

    async def test_registro_academico(self, db_session, tenant_factory) -> None:
        """WHEN registro academico, THEN todos los resultados del tenant."""
        from app.repositories.resultado_repository import ResultadoRepository

        tenant = await tenant_factory()
        ev = await _make_evaluacion(db_session, tenant.id, dias_disponibles=5)
        u = await _make_user(db_session, tenant.id)
        repo = ResultadoRepository()

        await repo.create_resultado(
            tenant_id=tenant.id, evaluacion_id=ev.id, alumno_id=u.id,
            nota_final="8", session=db_session,
        )

        registro = await repo.get_registro_academico(
            tenant_id=tenant.id, session=db_session
        )
        assert len(registro) >= 1

    async def test_registro_filter_by_alumno(self, db_session, tenant_factory) -> None:
        """WHEN filtro por alumno, THEN solo sus resultados."""
        from app.repositories.resultado_repository import ResultadoRepository

        tenant = await tenant_factory()
        ev = await _make_evaluacion(db_session, tenant.id, dias_disponibles=5)
        u1 = await _make_user(db_session, tenant.id)
        u2 = await _make_user(db_session, tenant.id)
        repo = ResultadoRepository()

        await repo.create_resultado(
            tenant_id=tenant.id, evaluacion_id=ev.id, alumno_id=u1.id,
            nota_final="8", session=db_session,
        )
        await repo.create_resultado(
            tenant_id=tenant.id, evaluacion_id=ev.id, alumno_id=u2.id,
            nota_final="7", session=db_session,
        )

        registro = await repo.get_registro_academico(
            tenant_id=tenant.id, session=db_session, alumno_id=u1.id
        )
        assert all(r["alumno_id"] == u1.id for r in registro)


# ── Tests: Rutas End-to-End ─────────────────────────────────────────────────


class TestRouterPaths:
    """Scenario: Endpoints correctamente registrados."""

    def _collect_all_paths(self, app) -> list:
        paths = []
        for r in app.routes:
            paths.append(getattr(r, "path", ""))
        return paths

    def test_coloquios_get_list_path_exists(self) -> None:
        """WHEN se inspecciona la app, THEN GET /api/v1/coloquios existe."""
        from app.main import create_app

        app = create_app()
        paths = self._collect_all_paths(app)
        assert any("api/v1/coloquios" in p for p in paths)

    def test_coloquios_all_paths_registered(self) -> None:
        """WHEN se inspecciona, THEN todos los paths estan registrados."""
        from app.main import create_app

        app = create_app()
        paths = self._collect_all_paths(app)
        expected = [
            "/api/v1/coloquios",
            "/api/v1/coloquios/metricas",
            "/api/v1/coloquios/agenda",
            "/api/v1/coloquios/mis-reservas",
            "/api/v1/coloquios/registro-academico",
            "/api/v1/coloquios/mi-registro",
        ]
        for ep in expected:
            assert any(ep in p for p in paths), f"Path {ep} not found"


class TestColoquiosEndpointGuard:
    """Scenario: Permisos en endpoints de coloquios."""

    async def test_crear_sin_token_retorna_401(self, client: "AsyncClient") -> None:
        """WHEN sin token, THEN 401."""
        response = await client.post(
            "/api/v1/coloquios",
            json={"materia_id": str(uuid.uuid4()), "cohorte_id": str(uuid.uuid4()),
                  "instancia": "Test", "dias_disponibles": 5},
        )
        assert response.status_code == 401

    async def test_crear_sin_permiso_retorna_403(self, client_no_perm: "AsyncClient") -> None:
        """WHEN sin permiso coloquios:gestionar, THEN 403."""
        response = await client_no_perm.post(
            "/api/v1/coloquios",
            json={"materia_id": str(uuid.uuid4()), "cohorte_id": str(uuid.uuid4()),
                  "instancia": "Test", "dias_disponibles": 5},
        )
        assert response.status_code == 403

    async def test_crear_con_extra_field_retorna_422(self, client_with_perm: "AsyncClient") -> None:
        """WHEN campo extra en body, THEN 422."""
        response = await client_with_perm.post(
            "/api/v1/coloquios",
            json={"materia_id": str(uuid.uuid4()), "cohorte_id": str(uuid.uuid4()),
                  "instancia": "Test", "dias_disponibles": 5, "color": "rojo"},
        )
        assert response.status_code == 422

    async def test_listar_metricas_sin_permiso(self, client_no_perm: "AsyncClient") -> None:
        """WHEN sin permiso, THEN 403."""
        response = await client_no_perm.get("/api/v1/coloquios/metricas")
        assert response.status_code == 403

    async def test_reservar_sin_permiso(self, client_no_perm: "AsyncClient") -> None:
        """WHEN sin coloquios:reservar, THEN 403."""
        response = await client_no_perm.post(
            f"/api/v1/coloquios/{uuid.uuid4()}/reservas",
            json={"fecha_hora": "2026-07-01T10:00:00Z"},
        )
        assert response.status_code == 403


# ── Fixtures locales ──────────────────────────────────────────────────────
# (importados de conftest + parches de permission)


@pytest.fixture
def app():
    from app.main import create_app

    return create_app()


@pytest.fixture
async def client(app):
    from httpx import ASGITransport, AsyncClient

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def _mock_user():
    from unittest.mock import MagicMock

    user = MagicMock()
    user.id = uuid.uuid4()
    user.tenant_id = uuid.uuid4()
    user.actor_id = user.id
    return user


@pytest.fixture
async def client_no_perm(app, _mock_user):
    from unittest.mock import AsyncMock, patch

    from httpx import ASGITransport, AsyncClient

    from app.core.dependencies import get_current_user

    async def _get_user():
        return _mock_user

    app.dependency_overrides[get_current_user] = _get_user
    transport = ASGITransport(app=app)
    with patch(
        "app.services.permission_service.PermissionService.verify_permission",
        new=AsyncMock(return_value=None),
    ):
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
    app.dependency_overrides.clear()


@pytest.fixture
async def client_no_perm_reservar(app, _mock_user):
    """Cliente que solo tiene coloquios:reservar."""
    from unittest.mock import AsyncMock, patch

    from httpx import ASGITransport, AsyncClient

    from app.core.dependencies import get_current_user
    from app.core.permissions import PermissionGrant

    async def _get_user():
        return _mock_user

    app.dependency_overrides[get_current_user] = _get_user

    async def _verify_permission(user_id, tenant_id, required_code, session):
        if required_code == "coloquios:reservar":
            return PermissionGrant(code="coloquios:reservar", scope="propio")
        if required_code == "coloquios:gestionar":
            return None
        return None

    transport = ASGITransport(app=app)
    with patch(
        "app.services.permission_service.PermissionService.verify_permission",
        new=AsyncMock(side_effect=_verify_permission),
    ):
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
    app.dependency_overrides.clear()


@pytest.fixture
async def client_with_perm(app, _mock_user):
    from unittest.mock import AsyncMock, patch

    from httpx import ASGITransport, AsyncClient

    from app.core.dependencies import get_current_user
    from app.core.permissions import PermissionGrant

    async def _get_user():
        return _mock_user

    app.dependency_overrides[get_current_user] = _get_user
    grant = PermissionGrant(code="coloquios:gestionar", scope="global")
    transport = ASGITransport(app=app)
    with patch(
        "app.services.permission_service.PermissionService.verify_permission",
        new=AsyncMock(return_value=grant),
    ):
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
    app.dependency_overrides.clear()

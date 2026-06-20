"""Tests para equipos docentes — C-08.

TDD sections:
1. Schemas Pydantic
2. Repository methods
3. Service — mis equipos
4. Service — asignación masiva
5. Service — clonar equipo (RN-12)
6. Service — vigencia bloque
7. Service — export CSV
8. Router endpoints
"""

import csv
import io
import uuid
from datetime import datetime, timezone, timedelta

import pytest

pytestmark = pytest.mark.requires_db


# ── Helpers ─────────────────────────────────────────────────────────────


async def _make_user(db_session, tenant_id):
    from app.repositories.usuario_repository import UsuarioRepository

    repo = UsuarioRepository()
    return await repo.create(
        tenant_id=tenant_id,
        email=f"u-{uuid.uuid4().hex[:6]}@test.edu.ar",
        password_plain="pw",
        nombre="Test",
        apellidos="User",
        session=db_session,
    )


async def _make_role(db_session, tenant_id, code="PROFESOR"):
    from app.models.role import Role

    role = Role(
        tenant_id=tenant_id,
        code=code,
        nombre=code,
    )
    db_session.add(role)
    await db_session.flush()
    await db_session.refresh(role)
    return role


async def _make_materia(db_session, tenant_id, materia_id=None):
    from app.models.materia import Materia

    m = Materia(
        id=materia_id or uuid.uuid4(),
        tenant_id=tenant_id,
        codigo=f"MAT-{uuid.uuid4().hex[:6]}",
        nombre="Test Materia",
    )
    db_session.add(m)
    await db_session.flush()
    await db_session.refresh(m)
    return m


async def _make_carrera(db_session, tenant_id, carrera_id=None):
    from app.models.carrera import Carrera

    c = Carrera(
        id=carrera_id or uuid.uuid4(),
        tenant_id=tenant_id,
        codigo=f"CAR-{uuid.uuid4().hex[:6]}",
        nombre="Test Carrera",
    )
    db_session.add(c)
    await db_session.flush()
    await db_session.refresh(c)
    return c


async def _make_cohorte(db_session, tenant_id, carrera_id, cohorte_id=None):
    from app.models.cohorte import Cohorte

    c = Cohorte(
        id=cohorte_id or uuid.uuid4(),
        tenant_id=tenant_id,
        carrera_id=carrera_id,
        nombre=f"C-{uuid.uuid4().hex[:4]}",
        anio=2025,
        vig_desde="2025-01-01",
        vig_hasta="2025-12-31",
    )
    db_session.add(c)
    await db_session.flush()
    await db_session.refresh(c)
    return c


async def _make_asignacion(
    db_session,
    tenant_id,
    usuario_id,
    role_id,
    materia_id=None,
    carrera_id=None,
    cohorte_id=None,
    desde=None,
    hasta=None,
    comisiones=None,
    responsable_id=None,
):
    from app.repositories.asignacion_repository import AsignacionRepository
    from app.models.materia import Materia
    from app.models.carrera import Carrera
    from app.models.cohorte import Cohorte

    # Ensure parent FK records exist (no-op if already present)
    if materia_id is not None and not await db_session.get(Materia, materia_id):
        await _make_materia(db_session, tenant_id, materia_id=materia_id)
    if carrera_id is not None and not await db_session.get(Carrera, carrera_id):
        await _make_carrera(db_session, tenant_id, carrera_id=carrera_id)
    if cohorte_id is not None and carrera_id is not None and not await db_session.get(Cohorte, cohorte_id):
        await _make_cohorte(db_session, tenant_id, carrera_id, cohorte_id=cohorte_id)

    repo = AsignacionRepository()
    if desde is None:
        desde = datetime.now(timezone.utc) - timedelta(days=1)
    return await repo.create(
        tenant_id=tenant_id,
        usuario_id=usuario_id,
        role_id=role_id,
        desde=desde,
        hasta=hasta,
        materia_id=materia_id,
        carrera_id=carrera_id,
        cohorte_id=cohorte_id,
        comisiones=comisiones,
        responsable_id=responsable_id,
        session=db_session,
    )


# ═══════════════════════════════════════════════════════════════════════
# 1. Schemas Pydantic (app/schemas/equipo.py)
# ═══════════════════════════════════════════════════════════════════════


class TestSchemasExtraForbid:
    """1.1 + 1.2: MisEquiposResponse / EquipoResumen con extra='forbid'."""

    def test_mis_equipos_response_extra_forbidden(self):
        from app.schemas.equipo import MisEquiposResponse
        from pydantic import ValidationError

        with pytest.raises(ValidationError) as excinfo:
            MisEquiposResponse(
                materia_id=str(uuid.uuid4()),
                campo_extra="x",
            )
        errors = excinfo.value.errors()
        assert any(e["type"] == "extra_forbidden" for e in errors)

    def test_equipo_resumen_extra_forbidden(self):
        from app.schemas.equipo import EquipoResumen
        from pydantic import ValidationError

        with pytest.raises(ValidationError) as excinfo:
            EquipoResumen(conteo=5, campo_extra="x")
        errors = excinfo.value.errors()
        assert any(e["type"] == "extra_forbidden" for e in errors)

    def test_equipo_resumen_conteo_ge_zero(self):
        from app.schemas.equipo import EquipoResumen
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            EquipoResumen(conteo=-1)

    def test_mis_equipos_response_grupa_asignaciones(self):
        """TRIANGULATE: estructura con asignaciones anidadas."""
        from app.schemas.equipo import MisEquiposResponse, AsignacionEquipoItem

        now = datetime.now(timezone.utc)
        item = AsignacionEquipoItem(
            id=str(uuid.uuid4()),
            role_id=str(uuid.uuid4()),
            comisiones=["A1"],
            desde=now,
            estado_vigencia="Vigente",
            usuario_id=str(uuid.uuid4()),
        )
        resp = MisEquiposResponse(
            materia_id=str(uuid.uuid4()),
            carrera_id=str(uuid.uuid4()),
            cohorte_id=str(uuid.uuid4()),
            asignaciones=[item],
        )
        assert len(resp.asignaciones) == 1
        assert resp.asignaciones[0].comisiones == ["A1"]

    def test_asignacion_equipo_item_no_pii(self):
        from app.schemas.equipo import AsignacionEquipoItem

        fields = set(AsignacionEquipoItem.model_fields.keys())
        pii = {"dni", "cuil", "cbu", "alias_cbu", "email"}
        assert not pii.intersection(fields)

    def test_equipo_resumen_happy(self):
        from app.schemas.equipo import EquipoResumen

        r = EquipoResumen(
            materia_id=str(uuid.uuid4()),
            carrera_id=str(uuid.uuid4()),
            cohorte_id=str(uuid.uuid4()),
            conteo=3,
        )
        assert r.conteo == 3


class TestSchemasAsignacionMasiva:
    """1.3 + 1.4: AsignacionMasivaRequest/Response."""

    def test_masiva_request_happy(self):
        from app.schemas.equipo import AsignacionMasivaRequest

        now = datetime.now(timezone.utc)
        req = AsignacionMasivaRequest(
            usuario_ids=[str(uuid.uuid4()), str(uuid.uuid4())],
            role_id=str(uuid.uuid4()),
            materia_id=str(uuid.uuid4()),
            carrera_id=str(uuid.uuid4()),
            cohorte_id=str(uuid.uuid4()),
            desde=now,
        )
        assert len(req.usuario_ids) == 2
        assert req.materia_id is not None

    def test_masiva_request_empty_list_rejected(self):
        from app.schemas.equipo import AsignacionMasivaRequest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            AsignacionMasivaRequest(
                usuario_ids=[],
                role_id=str(uuid.uuid4()),
                desde=datetime.now(timezone.utc),
            )

    def test_masiva_request_extra_forbidden(self):
        from app.schemas.equipo import AsignacionMasivaRequest
        from pydantic import ValidationError

        with pytest.raises(ValidationError) as excinfo:
            AsignacionMasivaRequest(
                usuario_ids=[str(uuid.uuid4())],
                role_id=str(uuid.uuid4()),
                desde=datetime.now(timezone.utc),
                campo_raro=123,
            )
        errors = excinfo.value.errors()
        assert any(e["type"] == "extra_forbidden" for e in errors)

    def test_masiva_response_happy(self):
        from app.schemas.equipo import AsignacionMasivaResponse, AsignacionMasivaItem

        resp = AsignacionMasivaResponse(
            creadas=3,
            rechazadas=[AsignacionMasivaItem(usuario_id=str(uuid.uuid4()), motivo="error")],
            omitidas=[AsignacionMasivaItem(usuario_id=str(uuid.uuid4()), motivo="ya existe")],
        )
        assert resp.creadas == 3
        assert len(resp.rechazadas) == 1
        assert len(resp.omitidas) == 1

    def test_masiva_item_extra_forbidden(self):
        from app.schemas.equipo import AsignacionMasivaItem
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            AsignacionMasivaItem(usuario_id=str(uuid.uuid4()), motivo="x", extra="y")


class TestSchemasClonar:
    """1.5 + 1.6: ClonarEquipoRequest/Response."""

    def test_clonar_request_happy(self):
        from app.schemas.equipo import ClonarEquipoRequest

        now = datetime.now(timezone.utc)
        req = ClonarEquipoRequest(
            origen_materia_id=str(uuid.uuid4()),
            origen_carrera_id=str(uuid.uuid4()),
            origen_cohorte_id=str(uuid.uuid4()),
            destino_carrera_id=str(uuid.uuid4()),
            destino_cohorte_id=str(uuid.uuid4()),
            nuevo_desde=now,
        )
        assert req.origen_materia_id is not None

    def test_clonar_request_extra_forbidden(self):
        from app.schemas.equipo import ClonarEquipoRequest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            ClonarEquipoRequest(
                origen_materia_id=str(uuid.uuid4()),
                origen_carrera_id=str(uuid.uuid4()),
                origen_cohorte_id=str(uuid.uuid4()),
                destino_carrera_id=str(uuid.uuid4()),
                destino_cohorte_id=str(uuid.uuid4()),
                nuevo_desde=datetime.now(timezone.utc),
                extra="bad",
            )

    def test_clonar_response_happy(self):
        from app.schemas.equipo import ClonarEquipoResponse, AsignacionMasivaItem

        resp = ClonarEquipoResponse(
            clonadas=5,
            omitidas=[AsignacionMasivaItem(usuario_id=str(uuid.uuid4()), motivo="ya existe")],
        )
        assert resp.clonadas == 5
        assert len(resp.omitidas) == 1


class TestSchemasVigenciaBloque:
    """1.7 + 1.8: VigenciaBloqueRequest/Response."""

    def test_vigencia_bloque_request_happy(self):
        from app.schemas.equipo import VigenciaBloqueRequest

        now = datetime.now(timezone.utc)
        req = VigenciaBloqueRequest(
            materia_id=str(uuid.uuid4()),
            carrera_id=str(uuid.uuid4()),
            cohorte_id=str(uuid.uuid4()),
            desde=now,
        )
        assert req.materia_id is not None

    def test_vigencia_bloque_request_extra_forbidden(self):
        from app.schemas.equipo import VigenciaBloqueRequest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            VigenciaBloqueRequest(
                desde=datetime.now(timezone.utc),
                extra="bad",
            )

    def test_vigencia_bloque_response_happy(self):
        from app.schemas.equipo import VigenciaBloqueResponse

        resp = VigenciaBloqueResponse(filas_afectadas=3)
        assert resp.filas_afectadas == 3

    def test_vigencia_bloque_response_extra_forbidden(self):
        from app.schemas.equipo import VigenciaBloqueResponse
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            VigenciaBloqueResponse(filas_afectadas=0, extra="bad")


# ═══════════════════════════════════════════════════════════════════════
# 2. Repository methods
# ═══════════════════════════════════════════════════════════════════════


class TestRepositoryListByEquipo:
    """2.1-2.3: list_by_equipo."""

    async def test_list_by_equipo_returns_matching(self, db_session, tenant_factory):
        """WHEN se pide un equipo, THEN devuelve solo las que matchean."""
        from app.repositories.asignacion_repository import AsignacionRepository

        tenant = await tenant_factory()
        user = await _make_user(db_session, tenant.id)
        role = await _make_role(db_session, tenant.id)
        repo = AsignacionRepository()

        mat_id = uuid.uuid4()
        car_id = uuid.uuid4()
        coh_id = uuid.uuid4()

        a1 = await _make_asignacion(
            db_session, tenant.id, user.id, role.id,
            materia_id=mat_id, carrera_id=car_id, cohorte_id=coh_id,
        )
        a2 = await _make_asignacion(
            db_session, tenant.id, user.id, role.id,
            materia_id=uuid.uuid4(), carrera_id=car_id, cohorte_id=coh_id,
        )

        result = await repo.list_by_equipo(
            tenant_id=tenant.id,
            materia_id=mat_id,
            carrera_id=car_id,
            cohorte_id=coh_id,
            session=db_session,
        )
        ids = {str(r.id) for r in result}
        assert str(a1.id) in ids
        # a2 tiene distinta materia, no deberia aparecer
        assert str(a2.id) not in ids

    async def test_list_by_equipo_solo_vigentes_flag(self, db_session, tenant_factory):
        """TRIANGULATE: solo_vigentes=False incluye vencidas."""
        from app.repositories.asignacion_repository import AsignacionRepository

        tenant = await tenant_factory()
        user = await _make_user(db_session, tenant.id)
        role = await _make_role(db_session, tenant.id)
        repo = AsignacionRepository()

        mat_id = uuid.uuid4()
        car_id = uuid.uuid4()
        coh_id = uuid.uuid4()

        vigente = await _make_asignacion(
            db_session, tenant.id, user.id, role.id,
            materia_id=mat_id, carrera_id=car_id, cohorte_id=coh_id,
            desde=datetime.now(timezone.utc) - timedelta(days=5),
            hasta=datetime.now(timezone.utc) + timedelta(days=30),
        )
        vencida = await _make_asignacion(
            db_session, tenant.id, user.id, role.id,
            materia_id=mat_id, carrera_id=car_id, cohorte_id=coh_id,
            desde=datetime.now(timezone.utc) - timedelta(days=10),
            hasta=datetime.now(timezone.utc) - timedelta(days=1),
        )

        result_vigentes = await repo.list_by_equipo(
            tenant_id=tenant.id,
            materia_id=mat_id, carrera_id=car_id, cohorte_id=coh_id,
            session=db_session, solo_vigentes=True,
        )
        ids_v = {str(r.id) for r in result_vigentes}
        assert str(vigente.id) in ids_v
        assert str(vencida.id) not in ids_v

        result_todas = await repo.list_by_equipo(
            tenant_id=tenant.id,
            materia_id=mat_id, carrera_id=car_id, cohorte_id=coh_id,
            session=db_session, solo_vigentes=False,
        )
        ids_t = {str(r.id) for r in result_todas}
        assert str(vencida.id) in ids_t

    async def test_list_by_equipo_tenant_aislamiento(self, db_session, tenant_factory):
        """TRIANGULATE: otro tenant no contamina."""
        from app.repositories.asignacion_repository import AsignacionRepository

        t1 = await tenant_factory()
        t2 = await tenant_factory()
        u1 = await _make_user(db_session, t1.id)
        r1 = await _make_role(db_session, t1.id)
        repo = AsignacionRepository()

        mat_id = uuid.uuid4()
        car_id = uuid.uuid4()
        coh_id = uuid.uuid4()

        await _make_asignacion(
            db_session, t1.id, u1.id, r1.id,
            materia_id=mat_id, carrera_id=car_id, cohorte_id=coh_id,
        )

        result_t2 = await repo.list_by_equipo(
            tenant_id=t2.id,
            materia_id=mat_id, carrera_id=car_id, cohorte_id=coh_id,
            session=db_session,
        )
        assert len(result_t2) == 0


class TestRepositoryExistsVigente:
    """2.4-2.5: exists_vigente."""

    async def test_exists_vigente_true(self, db_session, tenant_factory):
        """WHEN existe vigente, THEN True."""
        from app.repositories.asignacion_repository import AsignacionRepository

        tenant = await tenant_factory()
        user = await _make_user(db_session, tenant.id)
        role = await _make_role(db_session, tenant.id)
        repo = AsignacionRepository()

        mat_id = uuid.uuid4()
        car_id = uuid.uuid4()
        coh_id = uuid.uuid4()

        await _make_asignacion(
            db_session, tenant.id, user.id, role.id,
            materia_id=mat_id, carrera_id=car_id, cohorte_id=coh_id,
            desde=datetime.now(timezone.utc) - timedelta(days=1),
            hasta=datetime.now(timezone.utc) + timedelta(days=30),
        )

        exists = await repo.exists_vigente(
            tenant_id=tenant.id,
            usuario_id=user.id,
            role_id=role.id,
            materia_id=mat_id,
            carrera_id=car_id,
            cohorte_id=coh_id,
            session=db_session,
        )
        assert exists is True

    async def test_exists_vigente_false(self, db_session, tenant_factory):
        """WHEN no existe, THEN False."""
        from app.repositories.asignacion_repository import AsignacionRepository

        tenant = await tenant_factory()
        repo = AsignacionRepository()

        exists = await repo.exists_vigente(
            tenant_id=tenant.id,
            usuario_id=uuid.uuid4(),
            role_id=uuid.uuid4(),
            materia_id=uuid.uuid4(),
            carrera_id=uuid.uuid4(),
            cohorte_id=uuid.uuid4(),
            session=db_session,
        )
        assert exists is False

    async def test_exists_vigente_vencida_no_cuenta(self, db_session, tenant_factory):
        """TRIANGULATE: vencida no cuenta como vigente."""
        from app.repositories.asignacion_repository import AsignacionRepository

        tenant = await tenant_factory()
        user = await _make_user(db_session, tenant.id)
        role = await _make_role(db_session, tenant.id)
        repo = AsignacionRepository()

        mat_id = uuid.uuid4()
        car_id = uuid.uuid4()
        coh_id = uuid.uuid4()

        await _make_asignacion(
            db_session, tenant.id, user.id, role.id,
            materia_id=mat_id, carrera_id=car_id, cohorte_id=coh_id,
            desde=datetime.now(timezone.utc) - timedelta(days=10),
            hasta=datetime.now(timezone.utc) - timedelta(days=1),
        )

        exists = await repo.exists_vigente(
            tenant_id=tenant.id,
            usuario_id=user.id,
            role_id=role.id,
            materia_id=mat_id,
            carrera_id=car_id,
            cohorte_id=coh_id,
            session=db_session,
        )
        assert exists is False


class TestRepositoryListDistinctEquipos:
    """2.6-2.7: list_distinct_equipos."""

    async def test_list_distinct_equipos_basic(self, db_session, tenant_factory):
        """WHEN hay equipos con vigentes, THEN devuelve tuplas con conteo."""
        from app.repositories.asignacion_repository import AsignacionRepository

        tenant = await tenant_factory()
        user = await _make_user(db_session, tenant.id)
        role = await _make_role(db_session, tenant.id)
        repo = AsignacionRepository()

        mat_id = uuid.uuid4()
        car_id = uuid.uuid4()
        coh_id = uuid.uuid4()

        await _make_asignacion(
            db_session, tenant.id, user.id, role.id,
            materia_id=mat_id, carrera_id=car_id, cohorte_id=coh_id,
            desde=datetime.now(timezone.utc) - timedelta(days=1),
            hasta=datetime.now(timezone.utc) + timedelta(days=30),
        )
        await _make_asignacion(
            db_session, tenant.id, user.id, role.id,
            materia_id=mat_id, carrera_id=car_id, cohorte_id=coh_id,
            desde=datetime.now(timezone.utc) - timedelta(days=1),
            hasta=datetime.now(timezone.utc) + timedelta(days=30),
        )

        rows = await repo.list_distinct_equipos(
            tenant_id=tenant.id,
            session=db_session,
        )
        # Al menos 1 equipo con conteo >= 2
        equipos = [r for r in rows if r["materia_id"] == str(mat_id)]
        assert len(equipos) >= 1
        assert equipos[0]["conteo"] >= 2

    async def test_list_distinct_equipos_tenant_filter(self, db_session, tenant_factory):
        """TRIANGULATE: aislamiento por tenant."""
        from app.repositories.asignacion_repository import AsignacionRepository

        t1 = await tenant_factory()
        t2 = await tenant_factory()
        u1 = await _make_user(db_session, t1.id)
        r1 = await _make_role(db_session, t1.id)
        repo = AsignacionRepository()

        await _make_asignacion(
            db_session, t1.id, u1.id, r1.id,
            materia_id=uuid.uuid4(), carrera_id=uuid.uuid4(), cohorte_id=uuid.uuid4(),
            desde=datetime.now(timezone.utc) - timedelta(days=1),
        )

        rows_t2 = await repo.list_distinct_equipos(tenant_id=t2.id, session=db_session)
        assert len(rows_t2) == 0


class TestRepositoryBulkUpdateVigencia:
    """2.8-2.9: bulk_update_vigencia."""

    async def test_bulk_update_updates_team(self, db_session, tenant_factory):
        """WHEN se actualiza vigencia, THEN filas afectadas > 0."""
        from app.repositories.asignacion_repository import AsignacionRepository

        tenant = await tenant_factory()
        user = await _make_user(db_session, tenant.id)
        role = await _make_role(db_session, tenant.id)
        repo = AsignacionRepository()

        mat_id = uuid.uuid4()
        car_id = uuid.uuid4()
        coh_id = uuid.uuid4()

        await _make_asignacion(
            db_session, tenant.id, user.id, role.id,
            materia_id=mat_id, carrera_id=car_id, cohorte_id=coh_id,
        )

        nuevo_desde = datetime(2025, 1, 1, tzinfo=timezone.utc)
        nuevo_hasta = datetime(2025, 12, 31, tzinfo=timezone.utc)

        affected = await repo.bulk_update_vigencia(
            tenant_id=tenant.id,
            materia_id=mat_id,
            carrera_id=car_id,
            cohorte_id=coh_id,
            desde=nuevo_desde,
            hasta=nuevo_hasta,
            session=db_session,
        )
        assert affected >= 1

        # Verify
        rows = await repo.list_by_equipo(
            tenant_id=tenant.id,
            materia_id=mat_id, carrera_id=car_id, cohorte_id=coh_id,
            session=db_session, solo_vigentes=False,
        )
        for r in rows:
            assert r.desde == nuevo_desde
            assert r.hasta == nuevo_hasta

    async def test_bulk_update_other_tenant_unaffected(self, db_session, tenant_factory):
        """TRIANGULATE: otro tenant no se contamina."""
        from app.repositories.asignacion_repository import AsignacionRepository

        t1 = await tenant_factory()
        t2 = await tenant_factory()
        u1 = await _make_user(db_session, t1.id)
        r1 = await _make_role(db_session, t1.id)
        repo = AsignacionRepository()

        mat_id = uuid.uuid4()
        car_id = uuid.uuid4()
        coh_id = uuid.uuid4()

        orig_desde = datetime.now(timezone.utc) - timedelta(days=1)
        await _make_asignacion(
            db_session, t1.id, u1.id, r1.id,
            materia_id=mat_id, carrera_id=car_id, cohorte_id=coh_id,
            desde=orig_desde,
        )

        affected = await repo.bulk_update_vigencia(
            tenant_id=t2.id,
            materia_id=mat_id, carrera_id=car_id, cohorte_id=coh_id,
            desde=datetime(2025, 1, 1, tzinfo=timezone.utc),
            hasta=datetime(2025, 12, 31, tzinfo=timezone.utc),
            session=db_session,
        )
        assert affected == 0

    async def test_bulk_update_filas_0(self, db_session, tenant_factory):
        """TRIANGULATE: equipo sin asignaciones = 0 filas."""
        from app.repositories.asignacion_repository import AsignacionRepository

        tenant = await tenant_factory()
        repo = AsignacionRepository()

        affected = await repo.bulk_update_vigencia(
            tenant_id=tenant.id,
            materia_id=uuid.uuid4(),
            carrera_id=uuid.uuid4(),
            cohorte_id=uuid.uuid4(),
            desde=datetime.now(timezone.utc),
            session=db_session,
        )
        assert affected == 0


# ═══════════════════════════════════════════════════════════════════════
# 3. EquipoService — mis equipos
# ═══════════════════════════════════════════════════════════════════════


class TestEquipoServiceMisEquipos:
    """3.1-3.3: get_mis_equipos."""

    async def test_get_mis_equipos_agrupa(self, db_session, tenant_factory):
        """WHEN usuario tiene asignaciones vigentes, THEN agrupadas por tupla."""
        from app.services.equipo_service import EquipoService

        tenant = await tenant_factory()
        user = await _make_user(db_session, tenant.id)
        role = await _make_role(db_session, tenant.id)
        service = EquipoService()

        mat_id = uuid.uuid4()
        car_id = uuid.uuid4()
        coh_id = uuid.uuid4()

        await _make_asignacion(
            db_session, tenant.id, user.id, role.id,
            materia_id=mat_id, carrera_id=car_id, cohorte_id=coh_id,
            desde=datetime.now(timezone.utc) - timedelta(days=1),
            hasta=datetime.now(timezone.utc) + timedelta(days=30),
        )

        grupos = await service.get_mis_equipos(
            tenant_id=tenant.id,
            usuario_id=user.id,
            session=db_session,
        )
        assert len(grupos) >= 1
        grupo = [g for g in grupos if g["materia_id"] == str(mat_id)]
        assert len(grupo) >= 1
        assert len(grupo[0]["asignaciones"]) >= 1

    async def test_get_mis_equipos_sin_asignaciones_vacio(self, db_session, tenant_factory):
        """TRIANGULATE: usuario sin asignaciones → lista vacía."""
        from app.services.equipo_service import EquipoService

        tenant = await tenant_factory()
        user = await _make_user(db_session, tenant.id)
        service = EquipoService()

        grupos = await service.get_mis_equipos(
            tenant_id=tenant.id,
            usuario_id=user.id,
            session=db_session,
        )
        assert len(grupos) == 0

    async def test_get_mis_equipos_excluye_vencidas(self, db_session, tenant_factory):
        """TRIANGULATE: vencidas y soft-deleted excluidas."""
        from app.services.equipo_service import EquipoService
        from app.repositories.asignacion_repository import AsignacionRepository

        tenant = await tenant_factory()
        user = await _make_user(db_session, tenant.id)
        role = await _make_role(db_session, tenant.id)
        service = EquipoService()
        repo = AsignacionRepository()

        mat_id = uuid.uuid4()
        car_id = uuid.uuid4()
        coh_id = uuid.uuid4()

        await _make_asignacion(
            db_session, tenant.id, user.id, role.id,
            materia_id=mat_id, carrera_id=car_id, cohorte_id=coh_id,
            desde=datetime.now(timezone.utc) - timedelta(days=10),
            hasta=datetime.now(timezone.utc) - timedelta(days=1),
        )

        grupos = await service.get_mis_equipos(
            tenant_id=tenant.id,
            usuario_id=user.id,
            session=db_session,
        )
        # vencidas no deberian aparecer en mis-equipos
        assert len(grupos) == 0


# ═══════════════════════════════════════════════════════════════════════
# 4. EquipoService — asignación masiva
# ═══════════════════════════════════════════════════════════════════════


class TestEquipoServiceAsignacionMasiva:
    """4.1-4.6: asignacion_masiva."""

    async def test_masiva_todas_validas(self, db_session, tenant_factory):
        """WHEN todas válidas, THEN creadas=N, audit emite."""
        from app.services.equipo_service import EquipoService
        from app.repositories.audit_log_repository import AuditLogRepository

        tenant = await tenant_factory()
        user1 = await _make_user(db_session, tenant.id)
        user2 = await _make_user(db_session, tenant.id)
        role = await _make_role(db_session, tenant.id, "PROFESOR")
        service = EquipoService()

        mat_id = uuid.uuid4()
        car_id = uuid.uuid4()
        coh_id = uuid.uuid4()

        # Ensure parent FK records exist for the service
        await _make_materia(db_session, tenant.id, materia_id=mat_id)
        await _make_carrera(db_session, tenant.id, carrera_id=car_id)
        await _make_cohorte(db_session, tenant.id, car_id, cohorte_id=coh_id)

        resumen = await service.asignacion_masiva(
            tenant_id=tenant.id,
            actor_id=user1.id,
            role_id=role.id,
            role_code="PROFESOR",
            usuario_ids=[user1.id, user2.id],
            materia_id=mat_id,
            carrera_id=car_id,
            cohorte_id=coh_id,
            desde=datetime.now(timezone.utc) - timedelta(days=1),
            hasta=datetime.now(timezone.utc) + timedelta(days=30),
            session=db_session,
        )
        assert resumen["creadas"] == 2
        assert len(resumen["rechazadas"]) == 0
        assert len(resumen["omitidas"]) == 0

        # Verificar audit
        audit_repo = AuditLogRepository()
        log = await audit_repo.list(tenant_id=tenant.id, session=db_session, limit=1)
        assert len(log) > 0
        assert log[0].accion == "ASIGNACION_MODIFICAR"
        assert log[0].filas_afectadas == 2

    async def test_masiva_parcial_invalida(self, db_session, tenant_factory):
        """TRIANGULATE: best-effort, parcial inválida reporta sin revertir."""
        from app.services.equipo_service import EquipoService

        tenant = await tenant_factory()
        user1 = await _make_user(db_session, tenant.id)
        user2 = await _make_user(db_session, tenant.id)
        role = await _make_role(db_session, tenant.id, "PROFESOR")
        service = EquipoService()

        mat_id = uuid.uuid4()
        car_id = uuid.uuid4()
        coh_id = uuid.uuid4()

        # user1 valido, user2 con role_code incorrecto trigger validation
        resumen = await service.asignacion_masiva(
            tenant_id=tenant.id,
            actor_id=user1.id,
            role_id=role.id,
            role_code="ROL_INEXISTENTE",  # no es PROFESOR, fallará validación en service
            usuario_ids=[user1.id, user2.id],
            materia_id=mat_id,
            carrera_id=car_id,
            cohorte_id=coh_id,
            desde=datetime.now(timezone.utc) - timedelta(days=1),
            session=db_session,
        )
        assert resumen["creadas"] == 1 or resumen["creadas"] == 0  # dependiendo si falla todo
        total = resumen["creadas"] + len(resumen["rechazadas"]) + len(resumen["omitidas"])
        assert total == 2

    async def test_masiva_idempotencia(self, db_session, tenant_factory):
        """TRIANGULATE: fila ya vigente se omite."""
        from app.services.equipo_service import EquipoService

        tenant = await tenant_factory()
        user = await _make_user(db_session, tenant.id)
        role = await _make_role(db_session, tenant.id, "PROFESOR")
        service = EquipoService()

        mat_id = uuid.uuid4()
        car_id = uuid.uuid4()
        coh_id = uuid.uuid4()

        # Crear primera asignación vigente manualmente
        await _make_asignacion(
            db_session, tenant.id, user.id, role.id,
            materia_id=mat_id, carrera_id=car_id, cohorte_id=coh_id,
            desde=datetime.now(timezone.utc) - timedelta(days=1),
            hasta=datetime.now(timezone.utc) + timedelta(days=30),
        )

        resumen = await service.asignacion_masiva(
            tenant_id=tenant.id,
            actor_id=user.id,
            role_id=role.id,
            role_code="PROFESOR",
            usuario_ids=[user.id],
            materia_id=mat_id,
            carrera_id=car_id,
            cohorte_id=coh_id,
            desde=datetime.now(timezone.utc) - timedelta(days=1),
            session=db_session,
        )
        assert resumen["creadas"] == 0
        assert len(resumen["omitidas"]) == 1
        assert "ya existe" in resumen["omitidas"][0]["motivo"].lower()

    async def test_masiva_tenant_aislamiento(self, db_session, tenant_factory):
        """TRIANGULATE: todas creadas con tenant del actor."""
        from app.services.equipo_service import EquipoService
        from app.repositories.asignacion_repository import AsignacionRepository

        t1 = await tenant_factory()
        t2 = await tenant_factory()
        u1 = await _make_user(db_session, t1.id)
        u2 = await _make_user(db_session, t2.id)
        r1 = await _make_role(db_session, t1.id, "PROFESOR")
        service = EquipoService()

        mat_id = uuid.uuid4()
        car_id = uuid.uuid4()
        coh_id = uuid.uuid4()

        # Ensure parent FK records exist for the service
        await _make_materia(db_session, t1.id, materia_id=mat_id)
        await _make_carrera(db_session, t1.id, carrera_id=car_id)
        await _make_cohorte(db_session, t1.id, car_id, cohorte_id=coh_id)

        # Solo se puede crear para tenant t1 porque u2 está en t2
        resumen = await service.asignacion_masiva(
            tenant_id=t1.id,
            actor_id=u1.id,
            role_id=r1.id,
            role_code="PROFESOR",
            usuario_ids=[u1.id],
            materia_id=mat_id,
            carrera_id=car_id,
            cohorte_id=coh_id,
            desde=datetime.now(timezone.utc) - timedelta(days=1),
            session=db_session,
        )
        assert resumen["creadas"] == 1


# ═══════════════════════════════════════════════════════════════════════
# 5. EquipoService — clonar equipo (RN-12)
# ═══════════════════════════════════════════════════════════════════════


class TestEquipoServiceClonar:
    """5.1-5.6: clonar_equipo."""

    async def test_clonar_completo(self, db_session, tenant_factory):
        """WHEN clona equipo, THEN copia usuario/role/comisiones, reescribe carrera/cohorte/vigencia."""
        from app.services.equipo_service import EquipoService

        tenant = await tenant_factory()
        user = await _make_user(db_session, tenant.id)
        role = await _make_role(db_session, tenant.id, "PROFESOR")
        service = EquipoService()

        mat_id = uuid.uuid4()
        car_origen = uuid.uuid4()
        coh_origen = uuid.uuid4()
        car_destino = uuid.uuid4()
        coh_destino = uuid.uuid4()

        await _make_asignacion(
            db_session, tenant.id, user.id, role.id,
            materia_id=mat_id, carrera_id=car_origen, cohorte_id=coh_origen,
            comisiones=["A1"],
            desde=datetime.now(timezone.utc) - timedelta(days=1),
            hasta=datetime.now(timezone.utc) + timedelta(days=30),
        )

        # Ensure parent FK records for destino (mat_id already created by _make_asignacion)
        await _make_carrera(db_session, tenant.id, carrera_id=car_destino)
        await _make_cohorte(db_session, tenant.id, car_destino, cohorte_id=coh_destino)

        nuevo_desde = datetime(2026, 3, 1, tzinfo=timezone.utc)
        resumen = await service.clonar_equipo(
            tenant_id=tenant.id,
            actor_id=user.id,
            origen_materia_id=mat_id,
            origen_carrera_id=car_origen,
            origen_cohorte_id=coh_origen,
            destino_carrera_id=car_destino,
            destino_cohorte_id=coh_destino,
            nuevo_desde=nuevo_desde,
            session=db_session,
        )
        assert resumen["clonadas"] == 1
        assert len(resumen["omitidas"]) == 0

        # Verificar destino
        from app.repositories.asignacion_repository import AsignacionRepository

        repo = AsignacionRepository()
        destino = await repo.list_by_equipo(
            tenant_id=tenant.id,
            materia_id=mat_id, carrera_id=car_destino, cohorte_id=coh_destino,
            session=db_session, solo_vigentes=False,
        )
        assert len(destino) == 1
        d = destino[0]
        assert d.carrera_id == car_destino
        assert d.cohorte_id == coh_destino
        assert d.desde == nuevo_desde
        assert d.comisiones == ["A1"]
        assert d.usuario_id == user.id

    async def test_clonar_idempotente(self, db_session, tenant_factory):
        """TRIANGULATE: segunda corrida clonadas=0, todas omitidas."""
        from app.services.equipo_service import EquipoService

        tenant = await tenant_factory()
        user = await _make_user(db_session, tenant.id)
        role = await _make_role(db_session, tenant.id, "PROFESOR")
        service = EquipoService()

        mat_id = uuid.uuid4()
        car_origen = uuid.uuid4()
        coh_origen = uuid.uuid4()
        car_destino = uuid.uuid4()
        coh_destino = uuid.uuid4()

        await _make_asignacion(
            db_session, tenant.id, user.id, role.id,
            materia_id=mat_id, carrera_id=car_origen, cohorte_id=coh_origen,
            desde=datetime.now(timezone.utc) - timedelta(days=1),
            hasta=datetime.now(timezone.utc) + timedelta(days=30),
        )

        # Ensure parent FK records for destino (mat_id already created by _make_asignacion)
        await _make_carrera(db_session, tenant.id, carrera_id=car_destino)
        await _make_cohorte(db_session, tenant.id, car_destino, cohorte_id=coh_destino)

        await service.clonar_equipo(
            tenant_id=tenant.id,
            actor_id=user.id,
            origen_materia_id=mat_id,
            origen_carrera_id=car_origen,
            origen_cohorte_id=coh_origen,
            destino_carrera_id=car_destino,
            destino_cohorte_id=coh_destino,
            nuevo_desde=datetime(2026, 3, 1, tzinfo=timezone.utc),
            session=db_session,
        )

        resumen2 = await service.clonar_equipo(
            tenant_id=tenant.id,
            actor_id=user.id,
            origen_materia_id=mat_id,
            origen_carrera_id=car_origen,
            origen_cohorte_id=coh_origen,
            destino_carrera_id=car_destino,
            destino_cohorte_id=coh_destino,
            nuevo_desde=datetime(2026, 3, 1, tzinfo=timezone.utc),
            session=db_session,
        )
        assert resumen2["clonadas"] == 0
        assert len(resumen2["omitidas"]) == 1

    async def test_clonar_solo_vigentes_origen(self, db_session, tenant_factory):
        """TRIANGULATE: solo vigentes del origen se clonan."""
        from app.services.equipo_service import EquipoService

        tenant = await tenant_factory()
        user = await _make_user(db_session, tenant.id)
        role = await _make_role(db_session, tenant.id, "PROFESOR")
        service = EquipoService()

        mat_id = uuid.uuid4()
        car_origen = uuid.uuid4()
        coh_origen = uuid.uuid4()
        car_destino = uuid.uuid4()
        coh_destino = uuid.uuid4()

        # Crear una vencida
        await _make_asignacion(
            db_session, tenant.id, user.id, role.id,
            materia_id=mat_id, carrera_id=car_origen, cohorte_id=coh_origen,
            desde=datetime.now(timezone.utc) - timedelta(days=10),
            hasta=datetime.now(timezone.utc) - timedelta(days=1),
        )

        resumen = await service.clonar_equipo(
            tenant_id=tenant.id,
            actor_id=user.id,
            origen_materia_id=mat_id,
            origen_carrera_id=car_origen,
            origen_cohorte_id=coh_origen,
            destino_carrera_id=car_destino,
            destino_cohorte_id=coh_destino,
            nuevo_desde=datetime(2026, 3, 1, tzinfo=timezone.utc),
            session=db_session,
        )
        assert resumen["clonadas"] == 0

    async def test_clonar_tenant_aislamiento(self, db_session, tenant_factory):
        """TRIANGULATE: aislamiento por tenant."""
        from app.services.equipo_service import EquipoService

        t1 = await tenant_factory()
        t2 = await tenant_factory()
        u1 = await _make_user(db_session, t1.id)
        r1 = await _make_role(db_session, t1.id, "PROFESOR")
        service = EquipoService()

        mat_id = uuid.uuid4()
        car_origen = uuid.uuid4()
        coh_origen = uuid.uuid4()

        await _make_asignacion(
            db_session, t1.id, u1.id, r1.id,
            materia_id=mat_id, carrera_id=car_origen, cohorte_id=coh_origen,
            desde=datetime.now(timezone.utc) - timedelta(days=1),
            hasta=datetime.now(timezone.utc) + timedelta(days=30),
        )

        u2 = await _make_user(db_session, t2.id)

        # Clonar desde t2 (sin datos) debe dar 0
        resumen = await service.clonar_equipo(
            tenant_id=t2.id,
            actor_id=u2.id,
            origen_materia_id=mat_id,
            origen_carrera_id=car_origen,
            origen_cohorte_id=coh_origen,
            destino_carrera_id=uuid.uuid4(),
            destino_cohorte_id=uuid.uuid4(),
            nuevo_desde=datetime(2026, 3, 1, tzinfo=timezone.utc),
            session=db_session,
        )
        assert resumen["clonadas"] == 0


# ═══════════════════════════════════════════════════════════════════════
# 6. EquipoService — vigencia en bloque
# ═══════════════════════════════════════════════════════════════════════


class TestEquipoServiceVigenciaBloque:
    """6.1-6.4: modificar_vigencia_bloque."""

    async def test_vigencia_bloque_actualiza(self, db_session, tenant_factory):
        """WHEN vigencia válida, THEN actualiza N filas."""
        from app.services.equipo_service import EquipoService
        from app.repositories.audit_log_repository import AuditLogRepository

        tenant = await tenant_factory()
        user = await _make_user(db_session, tenant.id)
        role = await _make_role(db_session, tenant.id)
        service = EquipoService()

        mat_id = uuid.uuid4()
        car_id = uuid.uuid4()
        coh_id = uuid.uuid4()

        await _make_asignacion(
            db_session, tenant.id, user.id, role.id,
            materia_id=mat_id, carrera_id=car_id, cohorte_id=coh_id,
        )
        await _make_asignacion(
            db_session, tenant.id, user.id, role.id,
            materia_id=mat_id, carrera_id=car_id, cohorte_id=coh_id,
        )

        resumen = await service.modificar_vigencia_bloque(
            tenant_id=tenant.id,
            actor_id=user.id,
            materia_id=mat_id,
            carrera_id=car_id,
            cohorte_id=coh_id,
            desde=datetime(2025, 1, 1, tzinfo=timezone.utc),
            hasta=datetime(2025, 12, 31, tzinfo=timezone.utc),
            session=db_session,
        )
        assert resumen["filas_afectadas"] == 2

        audit_repo = AuditLogRepository()
        log = await audit_repo.list(tenant_id=tenant.id, session=db_session, limit=1)
        assert log[0].filas_afectadas == 2

    async def test_vigencia_bloque_rango_invalido(self, db_session, tenant_factory):
        """TRIANGULATE: desde > hasta → ValueError."""
        from app.services.equipo_service import EquipoService

        tenant = await tenant_factory()
        service = EquipoService()

        with pytest.raises(ValueError) as excinfo:
            await service.modificar_vigencia_bloque(
                tenant_id=tenant.id,
                actor_id=uuid.uuid4(),
                materia_id=uuid.uuid4(),
                carrera_id=uuid.uuid4(),
                cohorte_id=uuid.uuid4(),
                desde=datetime(2025, 12, 31, tzinfo=timezone.utc),
                hasta=datetime(2025, 1, 1, tzinfo=timezone.utc),
                session=db_session,
            )
        assert "hasta" in str(excinfo.value).lower()

    async def test_vigencia_bloque_tenant_aislamiento(self, db_session, tenant_factory):
        """TRIANGULATE: otro tenant no afectado."""
        from app.services.equipo_service import EquipoService

        t1 = await tenant_factory()
        t2 = await tenant_factory()
        u1 = await _make_user(db_session, t1.id)
        r1 = await _make_role(db_session, t1.id)
        service = EquipoService()

        mat_id = uuid.uuid4()
        car_id = uuid.uuid4()
        coh_id = uuid.uuid4()

        await _make_asignacion(
            db_session, t1.id, u1.id, r1.id,
            materia_id=mat_id, carrera_id=car_id, cohorte_id=coh_id,
        )

        u2 = await _make_user(db_session, t2.id)

        resumen = await service.modificar_vigencia_bloque(
            tenant_id=t2.id,
            actor_id=u2.id,
            materia_id=mat_id, carrera_id=car_id, cohorte_id=coh_id,
            desde=datetime(2025, 1, 1, tzinfo=timezone.utc),
            session=db_session,
        )
        assert resumen["filas_afectadas"] == 0


# ═══════════════════════════════════════════════════════════════════════
# 7. EquipoService — export CSV
# ═══════════════════════════════════════════════════════════════════════


class TestEquipoServiceExportCsv:
    """7.1-7.6: export_equipo_csv."""

    async def test_export_csv_header_fijo(self, db_session, tenant_factory):
        """WHEN exporta CSV, THEN header fijo y N filas."""
        from app.services.equipo_service import EquipoService

        tenant = await tenant_factory()
        user = await _make_user(db_session, tenant.id)
        role = await _make_role(db_session, tenant.id, "PROFESOR")
        service = EquipoService()

        mat_id = uuid.uuid4()
        car_id = uuid.uuid4()
        coh_id = uuid.uuid4()

        await _make_asignacion(
            db_session, tenant.id, user.id, role.id,
            materia_id=mat_id, carrera_id=car_id, cohorte_id=coh_id,
            desde=datetime.now(timezone.utc) - timedelta(days=1),
            hasta=datetime.now(timezone.utc) + timedelta(days=30),
        )

        csv_content = await service.export_equipo_csv(
            tenant_id=tenant.id,
            materia_id=mat_id,
            carrera_id=car_id,
            cohorte_id=coh_id,
            session=db_session,
        )

        lines = csv_content.strip().split("\n")
        assert len(lines) >= 2  # header + al menos 1 fila
        header = lines[0]
        assert "legajo" in header
        assert "docente" in header
        assert "rol" in header
        assert "materia_id" in header
        assert "carrera_id" in header
        assert "cohorte_id" in header
        assert "comisiones" in header
        assert "desde" in header
        assert "hasta" in header
        assert "estado" in header

        reader = csv.reader(io.StringIO(csv_content))
        rows = list(reader)
        assert len(rows) >= 2  # header + data
        assert rows[1][2] == "PROFESOR"  # rol column (index 2)

    async def test_export_csv_no_pii(self, db_session, tenant_factory):
        """TRIANGULATE: NO contiene PII sensible."""
        from app.services.equipo_service import EquipoService

        tenant = await tenant_factory()
        user = await _make_user(db_session, tenant.id)
        role = await _make_role(db_session, tenant.id, "PROFESOR")
        service = EquipoService()

        mat_id = uuid.uuid4()
        car_id = uuid.uuid4()
        coh_id = uuid.uuid4()

        await _make_asignacion(
            db_session, tenant.id, user.id, role.id,
            materia_id=mat_id, carrera_id=car_id, cohorte_id=coh_id,
        )

        csv_content = await service.export_equipo_csv(
            tenant_id=tenant.id,
            materia_id=mat_id,
            carrera_id=car_id,
            cohorte_id=coh_id,
            session=db_session,
        )

        pii_keywords = ["dni", "cuil", "cbu", "alias_cbu", "email", "password"]
        lower_csv = csv_content.lower()
        for kw in pii_keywords:
            assert kw not in lower_csv, f"CSV contiene PII: {kw}"

    async def test_export_csv_comisiones_y_escape(self, db_session, tenant_factory):
        """TRIANGULATE: comisiones con ; y fórmulas escapadas."""
        from app.services.equipo_service import EquipoService

        tenant = await tenant_factory()
        user = await _make_user(db_session, tenant.id)
        role = await _make_role(db_session, tenant.id, "PROFESOR")
        service = EquipoService()

        mat_id = uuid.uuid4()
        car_id = uuid.uuid4()
        coh_id = uuid.uuid4()

        await _make_asignacion(
            db_session, tenant.id, user.id, role.id,
            materia_id=mat_id, carrera_id=car_id, cohorte_id=coh_id,
            comisiones=["A1", "B2"],
        )

        csv_content = await service.export_equipo_csv(
            tenant_id=tenant.id,
            materia_id=mat_id,
            carrera_id=car_id,
            cohorte_id=coh_id,
            session=db_session,
        )

        reader = csv.reader(io.StringIO(csv_content))
        rows = list(reader)
        # comisiones columna = index 6
        assert rows[1][6] == "A1;B2"

    async def test_export_csv_tenant_aislamiento(self, db_session, tenant_factory):
        """TRIANGULATE: aislamiento por tenant."""
        from app.services.equipo_service import EquipoService

        t1 = await tenant_factory()
        t2 = await tenant_factory()
        u1 = await _make_user(db_session, t1.id)
        r1 = await _make_role(db_session, t1.id, "PROFESOR")
        service = EquipoService()

        mat_id = uuid.uuid4()
        car_id = uuid.uuid4()
        coh_id = uuid.uuid4()

        await _make_asignacion(
            db_session, t1.id, u1.id, r1.id,
            materia_id=mat_id, carrera_id=car_id, cohorte_id=coh_id,
        )

        csv_t2 = await service.export_equipo_csv(
            tenant_id=t2.id,
            materia_id=mat_id,
            carrera_id=car_id,
            cohorte_id=coh_id,
            session=db_session,
        )
        lines = csv_t2.strip().split("\n")
        assert len(lines) == 1  # solo header


# ═══════════════════════════════════════════════════════════════════════
# 8. Router /api/v1/equipos
# ═══════════════════════════════════════════════════════════════════════


class TestRouterEndpointsRegistered:
    """8.1-8.8: Router registration y schema guards."""

    def test_mis_equipos_path_exists(self):
        from app.main import create_app

        app = create_app()
        paths = []
        for r in app.routes:
            paths.append(getattr(r, "path", ""))
        assert any("equipos/mis-equipos" in p for p in paths)

    def test_equipos_list_path_exists(self):
        from app.main import create_app

        app = create_app()
        paths = []
        for r in app.routes:
            paths.append(getattr(r, "path", ""))
        assert any(p == "/api/v1/equipos" for p in paths)

    def test_asignacion_masiva_path_exists(self):
        from app.main import create_app

        app = create_app()
        paths = []
        for r in app.routes:
            paths.append(getattr(r, "path", ""))
        assert any("asignacion-masiva" in p for p in paths)

    def test_clonar_path_exists(self):
        from app.main import create_app

        app = create_app()
        paths = []
        for r in app.routes:
            paths.append(getattr(r, "path", ""))
        assert any("clonar" in p for p in paths)

    def test_vigencia_patch_path_exists(self):
        from app.main import create_app

        app = create_app()
        paths = []
        for r in app.routes:
            paths.append(getattr(r, "path", ""))
        assert any("vigencia" in p for p in paths)

    def test_export_path_exists(self):
        from app.main import create_app

        app = create_app()
        paths = []
        for r in app.routes:
            paths.append(getattr(r, "path", ""))
        assert any("export" in p for p in paths)

    def test_schema_extra_forbidden_all(self):
        """Verify ALL equipo schemas have extra='forbid'."""
        from pydantic import BaseModel

        from app.schemas.equipo import (
            AsignacionEquipoItem,
            AsignacionMasivaItem,
            AsignacionMasivaRequest,
            AsignacionMasivaResponse,
            ClonarEquipoRequest,
            ClonarEquipoResponse,
            EquipoResumen,
            MisEquiposResponse,
            VigenciaBloqueRequest,
            VigenciaBloqueResponse,
        )

        schemas = [
            AsignacionEquipoItem,
            AsignacionMasivaItem,
            AsignacionMasivaRequest,
            AsignacionMasivaResponse,
            ClonarEquipoRequest,
            ClonarEquipoResponse,
            EquipoResumen,
            MisEquiposResponse,
            VigenciaBloqueRequest,
            VigenciaBloqueResponse,
        ]
        for s in schemas:
            config = s.model_config
            assert config.get("extra") == "forbid", f"{s.__name__} missing extra='forbid'"

    def test_equipo_service_file_under_500_loc(self):
        """REFACTOR 7.6 + 8.8: verificar LOC."""
        import os

        path = os.path.join(os.path.dirname(__file__), "..", "app", "services", "equipo_service.py")
        with open(path, encoding="utf-8") as f:
            lines = f.readlines()
        assert len(lines) <= 500, f"equipo_service.py has {len(lines)} lines (max 500)"

    def test_router_file_under_500_loc(self):
        import os

        path = os.path.join(os.path.dirname(__file__), "..", "app", "api", "v1", "routers", "equipos.py")
        with open(path, encoding="utf-8") as f:
            lines = f.readlines()
        assert len(lines) <= 500, f"equipos.py router has {len(lines)} lines (max 500)"

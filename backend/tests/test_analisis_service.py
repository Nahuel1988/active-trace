"""Service tests for AnalisisService (C-11).

Strict TDD: RED → GREEN → TRIANGULATE → REFACTOR.
Requires --run-db (real PostgreSQL, no mocks).
"""

from __future__ import annotations

import uuid

import pytest

from app.models.asignacion import Asignacion
from app.models.calificacion import Calificacion, OrigenCalificacionDB, UmbralMateria
from app.models.padron import EntradaPadron, VersionPadron
from app.models.role import Role
from app.services.analisis_service import AnalisisService

pytestmark = pytest.mark.requires_db


def _make_calificacion(
    tenant_id: uuid.UUID,
    materia_id: uuid.UUID,
    entrada_padron_id: uuid.UUID,
    actividad: str,
    creado_por: uuid.UUID,
    nota_numerica: float | None = None,
    nota_textual: str | None = None,
) -> Calificacion:
    return Calificacion(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        entrada_padron_id=entrada_padron_id,
        materia_id=materia_id,
        actividad=actividad,
        nota_numerica=nota_numerica,
        nota_textual=nota_textual,
        origen=OrigenCalificacionDB.IMPORTADO,
        creado_por=creado_por,
    )


def _make_umbral(
    tenant_id: uuid.UUID,
    materia_id: uuid.UUID,
    asignacion_id: uuid.UUID,
    umbral_pct: int = 60,
    valores_aprobatorios: list[str] | None = None,
) -> UmbralMateria:
    return UmbralMateria(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        asignacion_id=asignacion_id,
        materia_id=materia_id,
        umbral_pct=umbral_pct,
        valores_aprobatorios=valores_aprobatorios or [],
    )


async def _make_asignacion(session, tenant_id, materia_id, user_id) -> Asignacion:
    from datetime import datetime, timezone
    role = Role(id=uuid.uuid4(), tenant_id=tenant_id, code="PROFESOR", nombre="Profesor")
    session.add(role)
    await session.flush()
    asignacion = Asignacion(
        id=uuid.uuid4(), tenant_id=tenant_id,
        usuario_id=user_id, role_id=role.id,
        materia_id=materia_id,
        desde=datetime.now(timezone.utc),
    )
    session.add(asignacion)
    await session.flush()
    return asignacion


async def _crear_vp_con_entradas(
    db_session,
    tenant_id: uuid.UUID,
    materia_id: uuid.UUID,
    cohorte_id: uuid.UUID,
    alumnos: list[dict],
) -> tuple[VersionPadron, list[EntradaPadron]]:
    vp = VersionPadron(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        materia_id=materia_id,
        cohorte_id=cohorte_id,
        activa=True,
        total_entradas=len(alumnos),
        origen="archivo",
    )
    db_session.add(vp)
    await db_session.flush()

    entradas = []
    for a in alumnos:
        ep = EntradaPadron(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            version_padron_id=vp.id,
            nombre=a["nombre"],
            apellidos=a["apellidos"],
            email_encrypted="cifrado:test",
            comision=a.get("comision", "A"),
            regional=a.get("regional", "Centro"),
        )
        db_session.add(ep)
        entradas.append(ep)

    await db_session.commit()
    for ep in entradas:
        await db_session.refresh(ep)
    await db_session.refresh(vp)
    return vp, entradas


# ============================================================================
# 2.1 — Atrasados Computation
# ============================================================================


class TestGetAtrasados:
    """AnalisisService.get_atrasados — tasks 2.1–2.6."""

    @pytest.fixture(autouse=True)
    async def setup(self, db_session, cohorte, user_factory):
        self.t, self.m, self.c = cohorte
        self.session = db_session
        self.service = AnalisisService()
        self.user = await user_factory(self.session, tenant_id=self.t.id)

    async def test_atrasados_numerico_below_threshold(self):
        vp, (ep,) = await _crear_vp_con_entradas(
            self.session, self.t.id, self.m.id, self.c.id,
            [{"nombre": "Juan", "apellidos": "Pérez"}],
        )
        calif = _make_calificacion(
            self.t.id, self.m.id, ep.id, "Parcial (Real)",
            creado_por=self.user.id, nota_numerica=45.0,
        )
        self.session.add(calif)
        asignacion = await _make_asignacion(self.session, self.t.id, self.m.id, self.user.id)
        umbral = _make_umbral(self.t.id, self.m.id, asignacion.id, umbral_pct=60)
        self.session.add(umbral)
        await self.session.commit()

        resultado = await self.service.get_atrasados(
            tenant_id=self.t.id, materia_id=self.m.id,
            cohorte_id=self.c.id, session=self.session,
        )

        assert resultado.total > 0
        assert resultado.items[0].clasificacion == "below_threshold"
        assert resultado.items[0].alumno_nombre == "Juan"

    async def test_atrasados_textual_non_passing(self):
        vp, (ep,) = await _crear_vp_con_entradas(
            self.session, self.t.id, self.m.id, self.c.id,
            [{"nombre": "María", "apellidos": "García"}],
        )
        calif = _make_calificacion(
            self.t.id, self.m.id, ep.id, "Estado",
            creado_por=self.user.id, nota_textual="Regular",
        )
        self.session.add(calif)
        asignacion = await _make_asignacion(self.session, self.t.id, self.m.id, self.user.id)
        umbral = _make_umbral(
            self.t.id, self.m.id, asignacion.id,
            valores_aprobatorios=["Aprobado", "Promocionado"],
        )
        self.session.add(umbral)
        await self.session.commit()

        resultado = await self.service.get_atrasados(
            tenant_id=self.t.id, materia_id=self.m.id,
            cohorte_id=self.c.id, session=self.session,
        )
        assert resultado.total > 0
        assert resultado.items[0].clasificacion == "below_threshold"

    async def test_atrasados_all_passing_not_atrasado(self):
        vp, (ep,) = await _crear_vp_con_entradas(
            self.session, self.t.id, self.m.id, self.c.id,
            [{"nombre": "Luis", "apellidos": "Martín"}],
        )
        calif = _make_calificacion(
            self.t.id, self.m.id, ep.id, "Parcial (Real)",
            creado_por=self.user.id, nota_numerica=85.0,
        )
        self.session.add(calif)
        asignacion = await _make_asignacion(self.session, self.t.id, self.m.id, self.user.id)
        umbral = _make_umbral(self.t.id, self.m.id, asignacion.id, umbral_pct=60)
        self.session.add(umbral)
        await self.session.commit()

        resultado = await self.service.get_atrasados(
            tenant_id=self.t.id, materia_id=self.m.id,
            cohorte_id=self.c.id, session=self.session,
        )
        assert resultado.total == 0

    async def test_atrasados_fallback_default_60(self):
        vp, (ep,) = await _crear_vp_con_entradas(
            self.session, self.t.id, self.m.id, self.c.id,
            [{"nombre": "Pedro", "apellidos": "Sánchez"}],
        )
        calif = _make_calificacion(
            self.t.id, self.m.id, ep.id, "Parcial (Real)",
            creado_por=self.user.id, nota_numerica=50.0,
        )
        self.session.add(calif)
        await self.session.commit()

        resultado = await self.service.get_atrasados(
            tenant_id=self.t.id, materia_id=self.m.id,
            cohorte_id=self.c.id, session=self.session,
        )
        assert resultado.total > 0
        assert resultado.items[0].clasificacion == "below_threshold"

    async def test_atrasados_no_data(self):
        resultado = await self.service.get_atrasados(
            tenant_id=self.t.id, materia_id=self.m.id,
            cohorte_id=uuid.uuid4(), session=self.session,
        )
        assert resultado.total == 0
        assert resultado.items == []

    async def test_atrasados_materia_not_found(self):
        resultado = await self.service.get_atrasados(
            tenant_id=self.t.id, materia_id=uuid.uuid4(),
            session=self.session,
        )
        assert resultado.items == []
        assert resultado.total == 0


# ============================================================================
# 3.1 — Ranking
# ============================================================================


class TestGetRanking:
    """AnalisisService.get_ranking — tasks 3.1–3.5."""

    @pytest.fixture(autouse=True)
    async def setup(self, db_session, cohorte, user_factory):
        self.t, self.m, self.c = cohorte
        self.session = db_session
        self.service = AnalisisService()
        self.user = await user_factory(self.session, tenant_id=self.t.id)

    async def test_ranking_descending_order(self):
        vp, entradas = await _crear_vp_con_entradas(
            self.session, self.t.id, self.m.id, self.c.id,
            [{"nombre": "Ana", "apellidos": "García"},
             {"nombre": "Luis", "apellidos": "Pérez"}],
        )
        ana, luis = entradas
        for c in [
            _make_calificacion(self.t.id, self.m.id, ana.id, "TP1", self.user.id, nota_numerica=80),
            _make_calificacion(self.t.id, self.m.id, ana.id, "TP2", self.user.id, nota_numerica=75),
            _make_calificacion(self.t.id, self.m.id, luis.id, "TP1", self.user.id, nota_numerica=80),
        ]:
            self.session.add(c)
        await self.session.commit()

        resultado = await self.service.get_ranking(
            tenant_id=self.t.id, materia_id=self.m.id,
            cohorte_id=self.c.id, session=self.session,
        )
        assert len(resultado.items) == 2
        assert resultado.items[0].alumno_nombre == "Ana"
        assert resultado.items[0].actividades_aprobadas == 2
        assert resultado.items[1].actividades_aprobadas == 1

    async def test_ranking_zero_approved_excluded(self):
        vp, entradas = await _crear_vp_con_entradas(
            self.session, self.t.id, self.m.id, self.c.id,
            [{"nombre": "Ana", "apellidos": "García"},
             {"nombre": "Luis", "apellidos": "Pérez"}],
        )
        ana, luis = entradas
        for c in [
            _make_calificacion(self.t.id, self.m.id, ana.id, "TP1", self.user.id, nota_numerica=80),
            _make_calificacion(self.t.id, self.m.id, luis.id, "TP1", self.user.id, nota_numerica=30),
        ]:
            self.session.add(c)
        asignacion = await _make_asignacion(self.session, self.t.id, self.m.id, self.user.id)
        umbral = _make_umbral(self.t.id, self.m.id, asignacion.id, umbral_pct=60)
        self.session.add(umbral)
        await self.session.commit()

        resultado = await self.service.get_ranking(
            tenant_id=self.t.id, materia_id=self.m.id,
            cohorte_id=self.c.id, session=self.session,
        )
        assert len(resultado.items) == 1
        assert resultado.items[0].alumno_nombre == "Ana"

    async def test_ranking_tie_breaking_alphabetical(self):
        vp, entradas = await _crear_vp_con_entradas(
            self.session, self.t.id, self.m.id, self.c.id,
            [{"nombre": "Bruno", "apellidos": "Díaz"},
             {"nombre": "Ana", "apellidos": "García"},
             {"nombre": "Carlos", "apellidos": "García"}],
        )
        bruno, ana, carlos = entradas
        for c in [
            _make_calificacion(self.t.id, self.m.id, bruno.id, "TP1", self.user.id, nota_numerica=80),
            _make_calificacion(self.t.id, self.m.id, ana.id, "TP1", self.user.id, nota_numerica=80),
            _make_calificacion(self.t.id, self.m.id, carlos.id, "TP1", self.user.id, nota_numerica=80),
        ]:
            self.session.add(c)
        await self.session.commit()

        resultado = await self.service.get_ranking(
            tenant_id=self.t.id, materia_id=self.m.id,
            cohorte_id=self.c.id, session=self.session,
        )
        assert len(resultado.items) == 3
        assert resultado.items[0].alumno_apellido == "Díaz"
        assert resultado.items[1].alumno_apellido == "García"
        assert resultado.items[1].alumno_nombre == "Ana"
        assert resultado.items[2].alumno_apellido == "García"
        assert resultado.items[2].alumno_nombre == "Carlos"


# ============================================================================
# 4.1 — Reporte Rápido
# ============================================================================


class TestGetReporteRapido:
    """AnalisisService.get_reporte_rapido — tasks 4.1–4.4."""

    @pytest.fixture(autouse=True)
    async def setup(self, db_session, cohorte, user_factory):
        self.t, self.m, self.c = cohorte
        self.session = db_session
        self.service = AnalisisService()
        self.user = await user_factory(self.session, tenant_id=self.t.id)

    async def test_reporte_con_datos(self):
        vp, entradas = await _crear_vp_con_entradas(
            self.session, self.t.id, self.m.id, self.c.id,
            [{"nombre": "Ana", "apellidos": "García"},
             {"nombre": "Luis", "apellidos": "Pérez"}],
        )
        ana, luis = entradas
        for c in [
            _make_calificacion(self.t.id, self.m.id, ana.id, "TP1", self.user.id, nota_numerica=80),
            _make_calificacion(self.t.id, self.m.id, ana.id, "TP2", self.user.id, nota_numerica=75),
            _make_calificacion(self.t.id, self.m.id, luis.id, "TP1", self.user.id, nota_numerica=30),
        ]:
            self.session.add(c)
        asignacion = await _make_asignacion(self.session, self.t.id, self.m.id, self.user.id)
        umbral = _make_umbral(self.t.id, self.m.id, asignacion.id, umbral_pct=60)
        self.session.add(umbral)
        await self.session.commit()

        resultado = await self.service.get_reporte_rapido(
            tenant_id=self.t.id, materia_id=self.m.id,
            cohorte_id=self.c.id, session=self.session,
        )
        assert resultado.total_alumnos == 2
        assert resultado.total_actividades == 2
        assert resultado.sin_datos is False

    async def test_reporte_sin_datos(self):
        resultado = await self.service.get_reporte_rapido(
            tenant_id=self.t.id, materia_id=self.m.id,
            cohorte_id=self.c.id, session=self.session,
        )
        assert resultado.sin_datos is True
        assert resultado.total_alumnos == 0
        assert resultado.total_actividades == 0


# ============================================================================
# 5.1 — Notas Finales
# ============================================================================


class TestGetNotasFinales:
    """AnalisisService.get_notas_finales — tasks 5.1–5.5."""

    @pytest.fixture(autouse=True)
    async def setup(self, db_session, cohorte, user_factory):
        self.t, self.m, self.c = cohorte
        self.session = db_session
        self.service = AnalisisService()
        self.user = await user_factory(self.session, tenant_id=self.t.id)

    async def test_notas_finales_con_promedio(self):
        vp, (ep,) = await _crear_vp_con_entradas(
            self.session, self.t.id, self.m.id, self.c.id,
            [{"nombre": "Ana", "apellidos": "García"}],
        )
        for c in [
            _make_calificacion(self.t.id, self.m.id, ep.id, "Parcial (Real)", self.user.id, nota_numerica=80),
            _make_calificacion(self.t.id, self.m.id, ep.id, "TP (Real)", self.user.id, nota_numerica=70),
        ]:
            self.session.add(c)
        await self.session.commit()

        resultado = await self.service.get_notas_finales(
            tenant_id=self.t.id, materia_id=self.m.id,
            cohorte_id=self.c.id, session=self.session,
        )
        assert len(resultado.items) == 1
        assert resultado.items[0].promedio_numerico == 75.0

    async def test_notas_finales_textuales_no_afectan_promedio(self):
        vp, (ep,) = await _crear_vp_con_entradas(
            self.session, self.t.id, self.m.id, self.c.id,
            [{"nombre": "Luis", "apellidos": "Pérez"}],
        )
        for c in [
            _make_calificacion(self.t.id, self.m.id, ep.id, "Parcial (Real)", self.user.id, nota_numerica=80),
            _make_calificacion(self.t.id, self.m.id, ep.id, "Estado", self.user.id, nota_textual="Aprobado"),
        ]:
            self.session.add(c)
        await self.session.commit()

        resultado = await self.service.get_notas_finales(
            tenant_id=self.t.id, materia_id=self.m.id,
            cohorte_id=self.c.id, session=self.session,
        )
        alumno = resultado.items[0]
        assert alumno.promedio_numerico == 80.0
        assert len(alumno.actividades_textuales) == 1

    async def test_notas_finales_csv_format(self):
        vp, (ep,) = await _crear_vp_con_entradas(
            self.session, self.t.id, self.m.id, self.c.id,
            [{"nombre": "Ana", "apellidos": "García"}],
        )
        self.session.add(_make_calificacion(
            self.t.id, self.m.id, ep.id, "Parcial (Real)", self.user.id, nota_numerica=85,
        ))
        await self.session.commit()

        resultado = await self.service.get_notas_finales(
            tenant_id=self.t.id, materia_id=self.m.id,
            cohorte_id=self.c.id, format="csv", session=self.session,
        )
        assert isinstance(resultado, str)
        assert "entrada_padron_id" in resultado
        assert "Ana" in resultado


# ============================================================================
# 6.1 — Entregas Pendientes
# ============================================================================


class TestGetEntregasPendientes:
    """AnalisisService.get_entregas_pendientes — tasks 6.1–6.5."""

    @pytest.fixture(autouse=True)
    async def setup(self, db_session, cohorte, user_factory):
        self.t, self.m, self.c = cohorte
        self.session = db_session
        self.service = AnalisisService()
        self.user = await user_factory(self.session, tenant_id=self.t.id)

    async def test_entregas_pendientes_textuales(self):
        vp, (ep,) = await _crear_vp_con_entradas(
            self.session, self.t.id, self.m.id, self.c.id,
            [{"nombre": "Ana", "apellidos": "García"}],
        )
        for c in [
            _make_calificacion(self.t.id, self.m.id, ep.id, "Parcial (Real)", self.user.id, nota_numerica=80),
            _make_calificacion(self.t.id, self.m.id, ep.id, "Estado", self.user.id, nota_textual="Aprobado"),
        ]:
            self.session.add(c)
        await self.session.commit()

        resultado = await self.service.get_entregas_pendientes(
            tenant_id=self.t.id, materia_id=self.m.id,
            cohorte_id=self.c.id, session=self.session,
        )
        assert resultado.todas_corregidas is True

    async def test_entregas_pendientes_con_pendientes(self):
        vp, (ep,) = await _crear_vp_con_entradas(
            self.session, self.t.id, self.m.id, self.c.id,
            [{"nombre": "Ana", "apellidos": "García"}],
        )
        self.session.add(_make_calificacion(
            self.t.id, self.m.id, ep.id, "Parcial (Real)", self.user.id, nota_numerica=80,
        ))
        await self.session.commit()

        resultado = await self.service.get_entregas_pendientes(
            tenant_id=self.t.id, materia_id=self.m.id,
            cohorte_id=self.c.id, session=self.session,
        )
        assert resultado.todas_corregidas is True

"""Service tests for MonitorService (C-11).

Requires --run-db (real PostgreSQL, no mocks).
"""

from __future__ import annotations

import uuid

import pytest

from datetime import datetime, timezone

from app.models.asignacion import Asignacion
from app.models.calificacion import Calificacion, OrigenCalificacionDB
from app.models.padron import EntradaPadron, VersionPadron
from app.models.role import Role
from app.services.monitor_service import MonitorService

pytestmark = pytest.mark.requires_db


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


class TestGetMonitorGeneral:
    """MonitorService.get_monitor_general — tasks 7.1, 7.2, 7.5."""

    @pytest.fixture(autouse=True)
    async def setup(self, db_session, cohorte, user_factory):
        self.t, self.m, self.c = cohorte
        self.session = db_session
        self.service = MonitorService()
        self.user = await user_factory(self.session, tenant_id=self.t.id)

    async def test_monitor_general_pagination(self):
        vp, entradas = await _crear_vp_con_entradas(
            self.session, self.t.id, self.m.id, self.c.id,
            [{"nombre": "Ana", "apellidos": "García"},
             {"nombre": "Luis", "apellidos": "Pérez"}],
        )
        await self.session.refresh(vp)

        resultado = await self.service.get_monitor_general(
            tenant_id=self.t.id, limit=1, offset=0, session=self.session,
        )
        assert resultado.total == 2
        assert len(resultado.items) == 1

    async def test_monitor_general_filtro_materia(self):
        vp, (ep,) = await _crear_vp_con_entradas(
            self.session, self.t.id, self.m.id, self.c.id,
            [{"nombre": "Ana", "apellidos": "García"}],
        )

        resultado = await self.service.get_monitor_general(
            tenant_id=self.t.id, materia_id=self.m.id, session=self.session,
        )
        assert len(resultado.items) == 1
        assert resultado.items[0].alumno_nombre == "Ana"

    async def test_monitor_general_filtro_q(self):
        vp, entradas = await _crear_vp_con_entradas(
            self.session, self.t.id, self.m.id, self.c.id,
            [{"nombre": "Ana", "apellidos": "García"},
             {"nombre": "Luis", "apellidos": "Pérez"}],
        )

        resultado = await self.service.get_monitor_general(
            tenant_id=self.t.id, q="García", session=self.session,
        )
        assert len(resultado.items) == 1
        assert resultado.items[0].alumno_apellido == "García"

    async def test_monitor_general_filtro_comision(self):
        vp, entradas = await _crear_vp_con_entradas(
            self.session, self.t.id, self.m.id, self.c.id,
            [{"nombre": "Ana", "apellidos": "García", "comision": "A"},
             {"nombre": "Luis", "apellidos": "Pérez", "comision": "B"}],
        )

        resultado = await self.service.get_monitor_general(
            tenant_id=self.t.id, comision="A", session=self.session,
        )
        assert len(resultado.items) == 1
        assert resultado.items[0].alumno_nombre == "Ana"


class TestGetMonitorSeguimiento:
    """MonitorService.get_monitor_seguimiento — tasks 7.3, 7.4, 7.5."""

    @pytest.fixture(autouse=True)
    async def setup(self, db_session, cohorte, user_factory):
        self.t, self.m, self.c = cohorte
        self.session = db_session
        self.service = MonitorService()
        self.user = await user_factory(self.session, tenant_id=self.t.id)
        self.other_user = await user_factory(
            self.session, tenant_id=self.t.id, email="other@example.com",
        )

    async def test_seguimiento_scoped_to_asignacion(self):
        vp, (ep,) = await _crear_vp_con_entradas(
            self.session, self.t.id, self.m.id, self.c.id,
            [{"nombre": "Ana", "apellidos": "García"}],
        )

        role = Role(id=uuid.uuid4(), tenant_id=self.t.id, code="PROFESOR", nombre="Profesor")
        self.session.add(role)
        await self.session.flush()

        asignacion = Asignacion(
            id=uuid.uuid4(), tenant_id=self.t.id,
            usuario_id=self.user.id, role_id=role.id,
            materia_id=self.m.id,
            desde=datetime.now(timezone.utc),
        )
        self.session.add(asignacion)
        await self.session.commit()

        resultado = await self.service.get_monitor_seguimiento(
            tenant_id=self.t.id, user_id=self.user.id, session=self.session,
        )
        assert len(resultado.items) == 1
        assert resultado.items[0].alumno_nombre == "Ana"

    async def test_seguimiento_exclude_other(self):
        resultado = await self.service.get_monitor_seguimiento(
            tenant_id=self.t.id, user_id=self.other_user.id, session=self.session,
        )
        assert len(resultado.items) == 0


class TestExportMonitorCSV:
    """MonitorService.export_monitor_csv — task 7.5."""

    @pytest.fixture(autouse=True)
    async def setup(self, db_session, cohorte, user_factory):
        self.t, self.m, self.c = cohorte
        self.session = db_session
        self.service = MonitorService()
        self.user = await user_factory(self.session, tenant_id=self.t.id)

    async def test_export_csv_has_header(self):
        vp, (ep,) = await _crear_vp_con_entradas(
            self.session, self.t.id, self.m.id, self.c.id,
            [{"nombre": "Ana", "apellidos": "García"}],
        )

        resultado = await self.service.get_monitor_general(
            tenant_id=self.t.id, session=self.session,
        )

        csv_content = await self.service.export_monitor_csv(
            tenant_id=self.t.id, items=resultado.items, session=self.session,
        )

        assert isinstance(csv_content, str)
        assert "alumno_nombre" in csv_content
        assert "Ana" in csv_content

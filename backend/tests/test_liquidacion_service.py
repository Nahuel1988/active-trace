"""Tests para LiquidacionService (C-18: cálculo, vista, cierre, historial).

TDD: RED → GREEN → TRIANGULATE → REFACTOR.
Requiere PostgreSQL (--run-db).
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

from app.models.asignacion import Asignacion
from app.models.carrera import Carrera, EstadoCarrera
from app.models.cohorte import Cohorte
from app.models.liquidacion import EstadoLiquidacion, Liquidacion
from app.models.role import Role
from app.models.salario_base import RolLiquidacion, SalarioBase
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.salario_base import SalarioBaseCreate
from app.schemas.salario_plus import SalarioPlusCreate
from app.services.grilla_service import GrillaService
from app.services.liquidacion_service import LiquidacionError, LiquidacionService

pytestmark = pytest.mark.requires_db


# ---------------------------------------------------------------------------
# Fixtures base
# ---------------------------------------------------------------------------


@pytest.fixture
async def tenant(db_session):
    t = Tenant(id=uuid.uuid4(), slug=f"t-{uuid.uuid4().hex[:8]}", nombre="Test", activo=True)
    db_session.add(t)
    await db_session.commit()
    await db_session.refresh(t)
    return t


@pytest.fixture
async def cohorte(db_session, tenant):
    car = Carrera(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        codigo="CAR01",
        nombre="Ingeniería",
        estado=EstadoCarrera.Activa,
    )
    db_session.add(car)
    await db_session.flush()

    c = Cohorte(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        carrera_id=car.id,
        nombre="2026",
        anio=2026,
        vig_desde="2026-01-01",
        vig_hasta="2026-12-31",
    )
    db_session.add(c)
    await db_session.commit()
    await db_session.refresh(c)
    return c


@pytest.fixture
async def role_profesor(db_session, tenant):
    r = Role(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        code="PROFESOR",
        nombre="Profesor",
    )
    db_session.add(r)
    await db_session.commit()
    await db_session.refresh(r)
    return r


@pytest.fixture
async def role_nexo(db_session, tenant):
    r = Role(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        code="NEXO",
        nombre="Nexo",
    )
    db_session.add(r)
    await db_session.commit()
    await db_session.refresh(r)
    return r


async def _crear_usuario(db_session, tenant_id, facturador=False, con_cbu=True):
    from app.core.security import encryption_service, email_lookup_hash

    email = f"doc-{uuid.uuid4().hex[:8]}@test.com"
    u = User(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        email_encrypted=encryption_service.encrypt(email),
        email_lookup=email_lookup_hash(email),
        password_hash="$argon2id$test",
        legajo=f"LEG-{uuid.uuid4().hex[:8]}",
        is_active=True,
        facturador=facturador,
        cbu_encrypted="cbu_cifrado" if con_cbu else None,
    )
    db_session.add(u)
    await db_session.flush()
    return u


async def _crear_asignacion(db_session, tenant_id, usuario_id, role_id, cohorte_id, comisiones=None):
    asig = Asignacion(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        usuario_id=usuario_id,
        role_id=role_id,
        cohorte_id=cohorte_id,
        desde=datetime(2026, 1, 1, tzinfo=timezone.utc),
        hasta=None,
        comisiones=comisiones or [],
    )
    db_session.add(asig)
    await db_session.flush()
    return asig


async def _crear_salario_base(db_session, tenant_id, rol, monto, grilla_svc=None):
    if grilla_svc is None:
        grilla_svc = GrillaService()
    data = SalarioBaseCreate(
        rol=RolLiquidacion(rol),
        monto=Decimal(str(monto)),
        desde=date(2026, 1, 1),
    )
    sb = await grilla_svc.configurar_salario_base(
        tenant_id=tenant_id, data=data, session=db_session
    )
    return sb


@pytest.fixture
def liq_service() -> LiquidacionService:
    return LiquidacionService()


@pytest.fixture
def grilla_svc() -> GrillaService:
    return GrillaService()


# ---------------------------------------------------------------------------
# Task 6.2 — Cálculo de liquidaciones
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_calcular_genera_liquidaciones(tenant, cohorte, role_profesor, liq_service, db_session):
    """RED: calcular genera Liquidacion para un docente con CBU."""
    await _crear_salario_base(db_session, tenant.id, "PROFESOR", 50000)
    docente = await _crear_usuario(db_session, tenant.id, con_cbu=True)
    await _crear_asignacion(db_session, tenant.id, docente.id, role_profesor.id, cohorte.id)
    await db_session.commit()

    resumen = await liq_service.calcular(
        tenant_id=tenant.id,
        cohorte_id=cohorte.id,
        periodo="2026-06",
        session=db_session,
    )
    await db_session.commit()

    assert resumen.cantidad_generada == 1
    assert resumen.docentes_omitidos_sin_cbu == 0
    assert resumen.total_general == Decimal("50000")


@pytest.mark.asyncio
async def test_calcular_omite_sin_cbu(tenant, cohorte, role_profesor, liq_service, db_session):
    """GREEN: docente sin CBU es omitido del cálculo."""
    await _crear_salario_base(db_session, tenant.id, "PROFESOR", 50000)
    docente_sin_cbu = await _crear_usuario(db_session, tenant.id, con_cbu=False)
    await _crear_asignacion(db_session, tenant.id, docente_sin_cbu.id, role_profesor.id, cohorte.id)
    await db_session.commit()

    resumen = await liq_service.calcular(
        tenant_id=tenant.id,
        cohorte_id=cohorte.id,
        periodo="2026-06",
        session=db_session,
    )
    await db_session.commit()

    assert resumen.cantidad_generada == 0
    assert resumen.docentes_omitidos_sin_cbu == 1


@pytest.mark.asyncio
async def test_calcular_facturador_marcado(tenant, cohorte, role_profesor, liq_service, db_session):
    """TRIANGULATE: docente facturador queda marcado como excluido_por_factura=True."""
    await _crear_salario_base(db_session, tenant.id, "PROFESOR", 50000)
    facturador = await _crear_usuario(db_session, tenant.id, facturador=True, con_cbu=True)
    await _crear_asignacion(db_session, tenant.id, facturador.id, role_profesor.id, cohorte.id)
    await db_session.commit()

    resumen = await liq_service.calcular(
        tenant_id=tenant.id,
        cohorte_id=cohorte.id,
        periodo="2026-06",
        session=db_session,
    )
    await db_session.commit()

    # La liquidación existe y fue marcada
    assert resumen.cantidad_generada == 1
    # Verificar directamente en la BD
    from sqlalchemy import select as sa_select
    result = await db_session.execute(
        sa_select(Liquidacion).where(
            Liquidacion.tenant_id == tenant.id,
            Liquidacion.usuario_id == facturador.id,
        )
    )
    liq = result.scalar_one_or_none()
    assert liq is not None
    assert liq.excluido_por_factura is True


@pytest.mark.asyncio
async def test_calcular_nexo_marcado(tenant, cohorte, role_nexo, liq_service, db_session):
    """TRIANGULATE: docente con rol NEXO queda marcado es_nexo=True."""
    await _crear_salario_base(db_session, tenant.id, "NEXO", 40000)
    nexo_user = await _crear_usuario(db_session, tenant.id, con_cbu=True)
    await _crear_asignacion(db_session, tenant.id, nexo_user.id, role_nexo.id, cohorte.id)
    await db_session.commit()

    await liq_service.calcular(
        tenant_id=tenant.id,
        cohorte_id=cohorte.id,
        periodo="2026-06",
        session=db_session,
    )
    await db_session.commit()

    from sqlalchemy import select as sa_select
    result = await db_session.execute(
        sa_select(Liquidacion).where(
            Liquidacion.tenant_id == tenant.id,
            Liquidacion.usuario_id == nexo_user.id,
        )
    )
    liq = result.scalar_one_or_none()
    assert liq is not None
    assert liq.es_nexo is True


@pytest.mark.asyncio
async def test_recalcular_reemplaza_abiertas(tenant, cohorte, role_profesor, liq_service, db_session):
    """TRIANGULATE: recalcular reemplaza liquidaciones Abiertas previas."""
    await _crear_salario_base(db_session, tenant.id, "PROFESOR", 50000)
    docente = await _crear_usuario(db_session, tenant.id, con_cbu=True)
    await _crear_asignacion(db_session, tenant.id, docente.id, role_profesor.id, cohorte.id)
    await db_session.commit()

    await liq_service.calcular(
        tenant_id=tenant.id, cohorte_id=cohorte.id, periodo="2026-06", session=db_session
    )
    await db_session.commit()

    # Segundo cálculo — no debe duplicar
    resumen2 = await liq_service.calcular(
        tenant_id=tenant.id, cohorte_id=cohorte.id, periodo="2026-06", session=db_session
    )
    await db_session.commit()
    assert resumen2.cantidad_generada == 1


@pytest.mark.asyncio
async def test_recalcular_rechazado_si_hay_cerradas(
    tenant, cohorte, role_profesor, liq_service, db_session
):
    """TRIANGULATE: recalcular lanza LiquidacionError 409 si existen Cerradas."""
    await _crear_salario_base(db_session, tenant.id, "PROFESOR", 50000)
    docente = await _crear_usuario(db_session, tenant.id, con_cbu=True)
    await _crear_asignacion(db_session, tenant.id, docente.id, role_profesor.id, cohorte.id)
    await db_session.commit()

    await liq_service.calcular(
        tenant_id=tenant.id, cohorte_id=cohorte.id, periodo="2026-06", session=db_session
    )
    await db_session.commit()

    # Cerrar la liquidación
    from sqlalchemy import select as sa_select
    result = await db_session.execute(
        sa_select(Liquidacion).where(
            Liquidacion.tenant_id == tenant.id,
            Liquidacion.cohorte_id == cohorte.id,
            Liquidacion.periodo == "2026-06",
        )
    )
    liq = result.scalar_one()
    await liq_service.cerrar(
        tenant_id=tenant.id, liquidacion_id=liq.id, session=db_session
    )
    await db_session.commit()

    # Intentar recalcular — debe fallar
    with pytest.raises(LiquidacionError) as exc_info:
        await liq_service.calcular(
            tenant_id=tenant.id, cohorte_id=cohorte.id, periodo="2026-06", session=db_session
        )
    assert exc_info.value.status_code == 409


@pytest.mark.asyncio
async def test_plus_aplicado_una_vez_por_clave(
    tenant, cohorte, role_profesor, liq_service, grilla_svc, db_session
):
    """PA-23: el plus se aplica UNA vez por clave (grupo, rol), sin tope."""
    await _crear_salario_base(db_session, tenant.id, "PROFESOR", 50000)

    # Crear plus para grupo PROG
    sp_data = SalarioPlusCreate(
        grupo="PROG",
        rol="PROFESOR",
        descripcion="Plus Prog",
        monto=Decimal("5000.00"),
        desde=date(2026, 1, 1),
    )
    await grilla_svc.configurar_salario_plus(
        tenant_id=tenant.id, data=sp_data, session=db_session
    )
    await db_session.commit()

    docente = await _crear_usuario(db_session, tenant.id, con_cbu=True)
    # Dos comisiones del mismo grupo PROG — debe aplicarse UNA vez
    await _crear_asignacion(
        db_session, tenant.id, docente.id, role_profesor.id, cohorte.id,
        comisiones=["PROG", "PROG"]
    )
    await db_session.commit()

    resumen = await liq_service.calcular(
        tenant_id=tenant.id, cohorte_id=cohorte.id, periodo="2026-06", session=db_session
    )
    await db_session.commit()

    from sqlalchemy import select as sa_select
    result = await db_session.execute(
        sa_select(Liquidacion).where(
            Liquidacion.tenant_id == tenant.id,
            Liquidacion.usuario_id == docente.id,
        )
    )
    liq = result.scalar_one()
    # monto_plus = 5000 (una vez, no dos)
    assert liq.monto_plus == Decimal("5000.00")
    assert liq.total == Decimal("55000.00")


# ---------------------------------------------------------------------------
# Task 7.2 — Vista segmentada, cierre, historial
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_segmentacion_correcta(tenant, cohorte, role_profesor, role_nexo, liq_service, db_session):
    """RED: obtener_liquidaciones retorna segmentos correctos."""
    await _crear_salario_base(db_session, tenant.id, "PROFESOR", 50000)
    await _crear_salario_base(db_session, tenant.id, "NEXO", 40000)

    normal = await _crear_usuario(db_session, tenant.id)
    facturador = await _crear_usuario(db_session, tenant.id, facturador=True)
    nexo_user = await _crear_usuario(db_session, tenant.id)

    await _crear_asignacion(db_session, tenant.id, normal.id, role_profesor.id, cohorte.id)
    await _crear_asignacion(db_session, tenant.id, facturador.id, role_profesor.id, cohorte.id)
    await _crear_asignacion(db_session, tenant.id, nexo_user.id, role_nexo.id, cohorte.id)
    await db_session.commit()

    await liq_service.calcular(
        tenant_id=tenant.id, cohorte_id=cohorte.id, periodo="2026-07", session=db_session
    )
    await db_session.commit()

    resp = await liq_service.obtener_liquidaciones(
        tenant_id=tenant.id, cohorte_id=cohorte.id, periodo="2026-07", session=db_session
    )

    assert len(resp.segmentos["general"].liquidaciones) == 1
    assert len(resp.segmentos["nexo"].liquidaciones) == 1
    assert len(resp.segmentos["facturantes"].liquidaciones) == 1


@pytest.mark.asyncio
async def test_kpis_suman_correctamente(tenant, cohorte, role_profesor, liq_service, db_session):
    """TRIANGULATE: KPIs total_sin_factura y total_con_factura son correctos."""
    await _crear_salario_base(db_session, tenant.id, "PROFESOR", 50000)

    normal = await _crear_usuario(db_session, tenant.id)
    facturador = await _crear_usuario(db_session, tenant.id, facturador=True)

    await _crear_asignacion(db_session, tenant.id, normal.id, role_profesor.id, cohorte.id)
    await _crear_asignacion(db_session, tenant.id, facturador.id, role_profesor.id, cohorte.id)
    await db_session.commit()

    await liq_service.calcular(
        tenant_id=tenant.id, cohorte_id=cohorte.id, periodo="2026-08", session=db_session
    )
    await db_session.commit()

    resp = await liq_service.obtener_liquidaciones(
        tenant_id=tenant.id, cohorte_id=cohorte.id, periodo="2026-08", session=db_session
    )

    assert resp.kpis.total_sin_factura == Decimal("50000")
    assert resp.kpis.total_con_factura == Decimal("50000")


@pytest.mark.asyncio
async def test_cerrar_liquidacion(tenant, cohorte, role_profesor, liq_service, db_session):
    """RED: cerrar cambia estado a Cerrada."""
    await _crear_salario_base(db_session, tenant.id, "PROFESOR", 50000)
    docente = await _crear_usuario(db_session, tenant.id, con_cbu=True)
    await _crear_asignacion(db_session, tenant.id, docente.id, role_profesor.id, cohorte.id)
    await db_session.commit()

    await liq_service.calcular(
        tenant_id=tenant.id, cohorte_id=cohorte.id, periodo="2026-09", session=db_session
    )
    await db_session.commit()

    from sqlalchemy import select as sa_select
    result = await db_session.execute(
        sa_select(Liquidacion).where(
            Liquidacion.tenant_id == tenant.id,
            Liquidacion.periodo == "2026-09",
        )
    )
    liq = result.scalar_one()

    resp = await liq_service.cerrar(
        tenant_id=tenant.id, liquidacion_id=liq.id, session=db_session
    )
    await db_session.commit()
    assert resp.estado == EstadoLiquidacion.Cerrada.value


@pytest.mark.asyncio
async def test_cerrar_dos_veces_rechazado(tenant, cohorte, role_profesor, liq_service, db_session):
    """TRIANGULATE: cerrar una Cerrada lanza LiquidacionError 409 (inmutable)."""
    await _crear_salario_base(db_session, tenant.id, "PROFESOR", 50000)
    docente = await _crear_usuario(db_session, tenant.id, con_cbu=True)
    await _crear_asignacion(db_session, tenant.id, docente.id, role_profesor.id, cohorte.id)
    await db_session.commit()

    await liq_service.calcular(
        tenant_id=tenant.id, cohorte_id=cohorte.id, periodo="2026-10", session=db_session
    )
    await db_session.commit()

    from sqlalchemy import select as sa_select
    result = await db_session.execute(
        sa_select(Liquidacion).where(
            Liquidacion.tenant_id == tenant.id,
            Liquidacion.periodo == "2026-10",
        )
    )
    liq = result.scalar_one()

    await liq_service.cerrar(tenant_id=tenant.id, liquidacion_id=liq.id, session=db_session)
    await db_session.commit()

    with pytest.raises(LiquidacionError) as exc_info:
        await liq_service.cerrar(tenant_id=tenant.id, liquidacion_id=liq.id, session=db_session)
    assert exc_info.value.status_code == 409


@pytest.mark.asyncio
async def test_historial_solo_cerradas(tenant, cohorte, role_profesor, liq_service, db_session):
    """TRIANGULATE: historial retorna solo las Cerradas."""
    await _crear_salario_base(db_session, tenant.id, "PROFESOR", 50000)
    d1 = await _crear_usuario(db_session, tenant.id, con_cbu=True)
    d2 = await _crear_usuario(db_session, tenant.id, con_cbu=True)
    await _crear_asignacion(db_session, tenant.id, d1.id, role_profesor.id, cohorte.id)
    await _crear_asignacion(db_session, tenant.id, d2.id, role_profesor.id, cohorte.id)
    await db_session.commit()

    await liq_service.calcular(
        tenant_id=tenant.id, cohorte_id=cohorte.id, periodo="2026-11", session=db_session
    )
    await db_session.commit()

    # Cerrar solo la de d1
    from sqlalchemy import select as sa_select
    result = await db_session.execute(
        sa_select(Liquidacion).where(
            Liquidacion.tenant_id == tenant.id,
            Liquidacion.periodo == "2026-11",
            Liquidacion.usuario_id == d1.id,
        )
    )
    liq_d1 = result.scalar_one()
    await liq_service.cerrar(tenant_id=tenant.id, liquidacion_id=liq_d1.id, session=db_session)
    await db_session.commit()

    historial = await liq_service.obtener_historial(
        tenant_id=tenant.id, periodo="2026-11", session=db_session
    )
    # Solo la de d1 debe aparecer
    assert len(historial) == 1
    assert historial[0].usuario_id == d1.id

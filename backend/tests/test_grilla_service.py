"""Tests para GrillaService (C-18: grilla-salarial-abm).

TDD: RED → GREEN → TRIANGULATE → REFACTOR.
Requiere PostgreSQL (--run-db).
"""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

import pytest

from app.models.salario_base import RolLiquidacion, SalarioBase
from app.models.salario_plus import SalarioPlus
from app.repositories.salario_base_repository import SolapamientoVigenciaError
from app.repositories.salario_plus_repository import SolapamientoPlusError
from app.schemas.salario_base import SalarioBaseCreate, SalarioBaseUpdate
from app.schemas.salario_plus import SalarioPlusCreate, SalarioPlusUpdate
from app.services.grilla_service import GrillaError, GrillaService

pytestmark = pytest.mark.requires_db


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
async def tenant(db_session):
    """Crea un tenant real en la BD."""
    from app.models.tenant import Tenant

    t = Tenant(id=uuid.uuid4(), slug=f"t-{uuid.uuid4().hex[:8]}", nombre="Test", activo=True)
    db_session.add(t)
    await db_session.commit()
    await db_session.refresh(t)
    return t


@pytest.fixture
def service() -> GrillaService:
    return GrillaService()


# ---------------------------------------------------------------------------
# SalarioBase — crear con solapamiento rechazado
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_crear_salario_base_exitoso(tenant, service, db_session):
    """RED: el servicio crea un SalarioBase y lo retorna con id."""
    data = SalarioBaseCreate(
        rol=RolLiquidacion.PROFESOR,
        monto=Decimal("50000.00"),
        desde=date(2026, 1, 1),
    )
    sb = await service.configurar_salario_base(
        tenant_id=tenant.id, data=data, session=db_session
    )
    await db_session.commit()
    assert sb.id is not None
    assert sb.tenant_id == tenant.id
    assert sb.rol == "PROFESOR"
    assert sb.monto == Decimal("50000.00")
    assert sb.hasta is None


@pytest.mark.asyncio
async def test_crear_salario_base_con_hasta(tenant, service, db_session):
    """TRIANGULATE: SalarioBase con vigencia cerrada."""
    data = SalarioBaseCreate(
        rol=RolLiquidacion.TUTOR,
        monto=Decimal("30000.00"),
        desde=date(2026, 1, 1),
        hasta=date(2026, 6, 30),
    )
    sb = await service.configurar_salario_base(
        tenant_id=tenant.id, data=data, session=db_session
    )
    await db_session.commit()
    assert sb.hasta == date(2026, 6, 30)


@pytest.mark.asyncio
async def test_crear_salario_base_solapamiento_rechazado(tenant, service, db_session):
    """RED/GREEN: solapamiento de vigencia lanza GrillaError 409."""
    data1 = SalarioBaseCreate(
        rol=RolLiquidacion.PROFESOR,
        monto=Decimal("50000.00"),
        desde=date(2026, 1, 1),
        hasta=date(2026, 12, 31),
    )
    await service.configurar_salario_base(tenant_id=tenant.id, data=data1, session=db_session)
    await db_session.commit()

    # Solapamiento parcial: empieza en junio, que cae dentro del primer rango
    data2 = SalarioBaseCreate(
        rol=RolLiquidacion.PROFESOR,
        monto=Decimal("55000.00"),
        desde=date(2026, 6, 1),
    )
    with pytest.raises(GrillaError) as exc_info:
        await service.configurar_salario_base(tenant_id=tenant.id, data=data2, session=db_session)
    assert exc_info.value.status_code == 409


@pytest.mark.asyncio
async def test_crear_salario_base_roles_distintos_no_solapan(tenant, service, db_session):
    """TRIANGULATE: diferentes roles no comparten solapamiento."""
    data_prof = SalarioBaseCreate(
        rol=RolLiquidacion.PROFESOR,
        monto=Decimal("50000.00"),
        desde=date(2026, 1, 1),
    )
    data_tutor = SalarioBaseCreate(
        rol=RolLiquidacion.TUTOR,
        monto=Decimal("30000.00"),
        desde=date(2026, 1, 1),
    )
    sb1 = await service.configurar_salario_base(tenant_id=tenant.id, data=data_prof, session=db_session)
    sb2 = await service.configurar_salario_base(tenant_id=tenant.id, data=data_tutor, session=db_session)
    await db_session.commit()
    assert sb1.id != sb2.id


# ---------------------------------------------------------------------------
# SalarioBase — obtener vigente por período
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_obtener_base_vigente_en_periodo(tenant, service, db_session):
    """RED: get_vigente retorna el salario del período correcto."""
    data = SalarioBaseCreate(
        rol=RolLiquidacion.PROFESOR,
        monto=Decimal("50000.00"),
        desde=date(2026, 1, 1),
    )
    await service.configurar_salario_base(tenant_id=tenant.id, data=data, session=db_session)
    await db_session.commit()

    vigente = await service.obtener_base_vigente(
        tenant_id=tenant.id, rol="PROFESOR", periodo="2026-06", session=db_session
    )
    assert vigente is not None
    assert vigente.rol == "PROFESOR"


@pytest.mark.asyncio
async def test_obtener_base_vigente_fuera_de_rango(tenant, service, db_session):
    """TRIANGULATE: no retorna nada si el período es anterior al inicio."""
    data = SalarioBaseCreate(
        rol=RolLiquidacion.COORDINADOR,
        monto=Decimal("70000.00"),
        desde=date(2026, 6, 1),
        hasta=date(2026, 12, 31),
    )
    await service.configurar_salario_base(tenant_id=tenant.id, data=data, session=db_session)
    await db_session.commit()

    # Enero 2026, antes del inicio de la vigencia
    vigente = await service.obtener_base_vigente(
        tenant_id=tenant.id, rol="COORDINADOR", periodo="2026-01", session=db_session
    )
    assert vigente is None


@pytest.mark.asyncio
async def test_obtener_base_vigente_despues_de_hasta(tenant, service, db_session):
    """TRIANGULATE: no retorna nada si el período supera el 'hasta'."""
    data = SalarioBaseCreate(
        rol=RolLiquidacion.NEXO,
        monto=Decimal("40000.00"),
        desde=date(2026, 1, 1),
        hasta=date(2026, 3, 31),
    )
    await service.configurar_salario_base(tenant_id=tenant.id, data=data, session=db_session)
    await db_session.commit()

    # Junio 2026, después del cierre
    vigente = await service.obtener_base_vigente(
        tenant_id=tenant.id, rol="NEXO", periodo="2026-06", session=db_session
    )
    assert vigente is None


# ---------------------------------------------------------------------------
# SalarioPlus — creación y solapamiento
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_crear_salario_plus_exitoso(tenant, service, db_session):
    """RED: el servicio crea un SalarioPlus y lo retorna con id."""
    data = SalarioPlusCreate(
        grupo="PROG",
        rol="PROFESOR",
        descripcion="Plus programación",
        monto=Decimal("5000.00"),
        desde=date(2026, 1, 1),
    )
    sp = await service.configurar_salario_plus(
        tenant_id=tenant.id, data=data, session=db_session
    )
    await db_session.commit()
    assert sp.id is not None
    assert sp.grupo == "PROG"
    assert sp.rol == "PROFESOR"


@pytest.mark.asyncio
async def test_crear_salario_plus_solapamiento_rechazado(tenant, service, db_session):
    """TRIANGULATE: solapamiento de plus para mismo (grupo, rol) lanza GrillaError 409."""
    data1 = SalarioPlusCreate(
        grupo="BD",
        rol="PROFESOR",
        descripcion="Plus BD v1",
        monto=Decimal("3000.00"),
        desde=date(2026, 1, 1),
        hasta=date(2026, 12, 31),
    )
    await service.configurar_salario_plus(tenant_id=tenant.id, data=data1, session=db_session)
    await db_session.commit()

    data2 = SalarioPlusCreate(
        grupo="BD",
        rol="PROFESOR",
        descripcion="Plus BD v2",
        monto=Decimal("3500.00"),
        desde=date(2026, 6, 1),
    )
    with pytest.raises(GrillaError) as exc_info:
        await service.configurar_salario_plus(tenant_id=tenant.id, data=data2, session=db_session)
    assert exc_info.value.status_code == 409


@pytest.mark.asyncio
async def test_crear_salario_plus_grupos_distintos_no_solapan(tenant, service, db_session):
    """TRIANGULATE: grupos distintos no comparten solapamiento."""
    data_prog = SalarioPlusCreate(
        grupo="PROG",
        rol="TUTOR",
        descripcion="Plus prog",
        monto=Decimal("2000.00"),
        desde=date(2026, 1, 1),
    )
    data_mat = SalarioPlusCreate(
        grupo="MAT",
        rol="TUTOR",
        descripcion="Plus mat",
        monto=Decimal("1500.00"),
        desde=date(2026, 1, 1),
    )
    sp1 = await service.configurar_salario_plus(tenant_id=tenant.id, data=data_prog, session=db_session)
    sp2 = await service.configurar_salario_plus(tenant_id=tenant.id, data=data_mat, session=db_session)
    await db_session.commit()
    assert sp1.id != sp2.id


@pytest.mark.asyncio
async def test_obtener_plus_vigentes_por_grupos(tenant, service, db_session):
    """GREEN/TRIANGULATE: obtener_plus_vigentes retorna los correctos para la lista de grupos."""
    for grupo in ["PROG", "BD", "ARQ"]:
        data = SalarioPlusCreate(
            grupo=grupo,
            rol="PROFESOR",
            descripcion=f"Plus {grupo}",
            monto=Decimal("2000.00"),
            desde=date(2026, 1, 1),
        )
        await service.configurar_salario_plus(tenant_id=tenant.id, data=data, session=db_session)
    await db_session.commit()

    plus_list = await service.obtener_plus_vigentes(
        tenant_id=tenant.id,
        grupos=["PROG", "BD"],
        rol="PROFESOR",
        periodo="2026-06",
        session=db_session,
    )
    grupos_obtenidos = {sp.grupo for sp in plus_list}
    assert "PROG" in grupos_obtenidos
    assert "BD" in grupos_obtenidos
    assert "ARQ" not in grupos_obtenidos
    assert len(plus_list) == 2

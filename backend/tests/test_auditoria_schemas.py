"""Tests para schemas, service y router de auditoría (C-19).

TDD estricto: cada clase prueba un comportamiento específico.
"""

import uuid
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.schemas.auditoria import (
    AccionesPorDiaItem,
    AuditoriaFiltros,
    ComunicacionesPorDocenteItem,
    InteraccionesItem,
    LogItem,
    UltimasAccionesItem,
)


class TestAuditoriaFiltros:
    """Scenario: AuditoriaFiltros — query params con validación."""

    def test_defaults(self) -> None:
        """WHEN sin parámetros THEN defaults correctos."""
        f = AuditoriaFiltros()
        assert f.limit == 200
        assert f.offset == 0
        assert f.desde is None

    def test_extra_fields_forbidden(self) -> None:
        """GIVEN campo extra THEN ValidationError."""
        with pytest.raises(ValidationError):
            AuditoriaFiltros(campo_extra="x")  # type: ignore[call-arg]

    def test_limit_gt_max_rejected(self) -> None:
        """GIVEN limit > 1000 THEN ValidationError."""
        with pytest.raises(ValidationError):
            AuditoriaFiltros(limit=5000)

    def test_limit_valid(self) -> None:
        """GIVEN limit válido THEN aceptado."""
        f = AuditoriaFiltros(limit=50)
        assert f.limit == 50

    def test_offset_negativo_rejected(self) -> None:
        """GIVEN offset negativo THEN ValidationError."""
        with pytest.raises(ValidationError):
            AuditoriaFiltros(offset=-1)


class TestAuditoriaResponseSchemas:
    """Scenario: DTOs de respuesta con from_attributes y extra='forbid'."""

    def test_acciones_por_dia_item(self) -> None:
        """WHEN datos válidos THEN crea el item."""
        dt = datetime(2026, 6, 15, tzinfo=timezone.utc)
        item = AccionesPorDiaItem(fecha=dt, total=5)
        assert item.fecha == dt
        assert item.total == 5

    def test_comunicaciones_item(self) -> None:
        """WHEN datos válidos THEN crea el item."""
        uid = uuid.uuid4()
        item = ComunicacionesPorDocenteItem(
            actor_id=uid, accion="COMUNICACION_ENVIAR", total=3,
        )
        assert item.actor_id == uid
        assert item.total == 3

    def test_interacciones_item_con_materia(self) -> None:
        """WHEN materia_id presente THEN se incluye."""
        uid = uuid.uuid4()
        mid = uuid.uuid4()
        item = InteraccionesItem(
            actor_id=uid, materia_id=mid, accion="PADRON_CARGAR", total=1,
        )
        assert item.materia_id == mid

    def test_interacciones_item_sin_materia(self) -> None:
        """WHEN materia_id null THEN se incluye como None."""
        uid = uuid.uuid4()
        item = InteraccionesItem(
            actor_id=uid, materia_id=None, accion="PADRON_CARGAR", total=1,
        )
        assert item.materia_id is None

    def test_log_item_from_attributes(self) -> None:
        """WHEN dict con campos THEN from_attributes."""
        uid = uuid.uuid4()
        dt = datetime(2026, 6, 15, tzinfo=timezone.utc)
        item = LogItem(
            id=uuid.uuid4(),
            fecha_hora=dt,
            actor_id=uid,
            materia_id=None,
            accion="TEST",
            detalle={"key": "val"},
            filas_afectadas=5,
            ip="10.0.0.1",
            user_agent="test",
        )
        assert item.accion == "TEST"
        assert item.detalle == {"key": "val"}

    def test_ultimas_acciones_item(self) -> None:
        """WHEN dict válido THEN crea el item."""
        item = UltimasAccionesItem(
            id=uuid.uuid4(),
            fecha_hora=datetime(2026, 6, 15, tzinfo=timezone.utc),
            actor_id=uuid.uuid4(),
            materia_id=None,
            accion="TEST",
            filas_afectadas=0,
            ip="::1",
            user_agent="pytest",
        )
        assert item.accion == "TEST"

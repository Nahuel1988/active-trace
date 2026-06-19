"""Tests para AuditCodes — catálogo de códigos de acción auditables.

TDD Cycle 1: RED → audit_codes module doesn't exist yet.
"""

import pytest

from app.core.audit_codes import AuditCodes


class TestAuditCodesValues:
    """Scenario: Cada código es un string con el valor exacto esperado."""

    def test_calificaciones_importar_value(self) -> None:
        assert AuditCodes.CALIFICACIONES_IMPORTAR == "CALIFICACIONES_IMPORTAR"

    def test_padron_cargar_value(self) -> None:
        assert AuditCodes.PADRON_CARGAR == "PADRON_CARGAR"

    def test_comunicacion_enviar_value(self) -> None:
        assert AuditCodes.COMUNICACION_ENVIAR == "COMUNICACION_ENVIAR"

    def test_asignacion_modificar_value(self) -> None:
        assert AuditCodes.ASIGNACION_MODIFICAR == "ASIGNACION_MODIFICAR"

    def test_liquidacion_cerrar_value(self) -> None:
        assert AuditCodes.LIQUIDACION_CERRAR == "LIQUIDACION_CERRAR"

    def test_impersonacion_iniciar_value(self) -> None:
        assert AuditCodes.IMPERSONACION_INICIAR == "IMPERSONACION_INICIAR"

    def test_impersonacion_finalizar_value(self) -> None:
        assert AuditCodes.IMPERSONACION_FINALIZAR == "IMPERSONACION_FINALIZAR"

    def test_coloquio_modificar_resultado_value(self) -> None:
        assert AuditCodes.COLOQUIO_MODIFICAR_RESULTADO == "COLOQUIO_MODIFICAR_RESULTADO"


class TestAuditCodesType:
    """Scenario: AuditCodes expone cada código como atributo de clase (str)."""

    def test_all_codes_are_strings(self) -> None:
        codes = [
            AuditCodes.CALIFICACIONES_IMPORTAR,
            AuditCodes.PADRON_CARGAR,
            AuditCodes.COMUNICACION_ENVIAR,
            AuditCodes.ASIGNACION_MODIFICAR,
            AuditCodes.LIQUIDACION_CERRAR,
            AuditCodes.IMPERSONACION_INICIAR,
            AuditCodes.IMPERSONACION_FINALIZAR,
            AuditCodes.COLOQUIO_MODIFICAR_RESULTADO,
        ]
        for code in codes:
            assert isinstance(code, str), f"Expected str, got {type(code)}"

    def test_can_pass_as_function_argument(self) -> None:
        """Verify that codes can be used as typed arguments."""

        def _log_action(accion: str) -> str:
            return f"action:{accion}"

        result = _log_action(AuditCodes.PADRON_CARGAR)
        assert result == "action:PADRON_CARGAR"

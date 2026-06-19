"""Tests para el decorator @audited — TDD Cycle 5.

RED: decorator no existe → tests fallan (no pueden importar).
GREEN: se implementa @audited en audit.py → tests pasan.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import AuditCodes, audited
from app.core.audit_codes import _AuditCodes


class TestAuditedDecoratorSuccess:
    """Scenario: endpoint decorado con @audited se completa con éxito."""

    async def test_successful_endpoint_calls_audit_action(self) -> None:
        """WHEN endpoint decorado completa sin error,
        THEN audit_action es llamada con la accion correcta."""
        mock_user = MagicMock()
        mock_user.id = uuid.uuid4()
        mock_user.tenant_id = uuid.uuid4()
        mock_user.impersonated = False

        @audited("TEST_ACCION")
        async def fake_endpoint(
            request: Request | None = None,
            current_user: object = None,
            db: AsyncSession | None = None,
            **kwargs: object,
        ) -> dict:
            return {"ok": True}

        with patch(
            "app.core.audit.audit_action",
            new_callable=AsyncMock,
        ) as mock_audit:
            result = await fake_endpoint(
                request=MagicMock(spec=Request),
                current_user=mock_user,
                db=MagicMock(spec=AsyncSession),
            )

        assert result == {"ok": True}
        mock_audit.assert_awaited_once()
        call_kwargs = mock_audit.await_args[1]  # **kwargs dict
        assert call_kwargs["accion"] == "TEST_ACCION"
        assert call_kwargs["filas_afectadas"] == 0

    async def test_filas_afectadas_from_response(self) -> None:
        """WHEN response tiene _filas_afectadas,
        THEN se usa ese valor en audit_action."""
        mock_user = MagicMock()
        mock_user.id = uuid.uuid4()
        mock_user.tenant_id = uuid.uuid4()
        mock_user.impersonated = False

        @audited("TEST_ACCION")
        async def fake_endpoint(
            request: Request | None = None,
            current_user: object = None,
            db: AsyncSession | None = None,
            **kwargs: object,
        ) -> dict:
            return {"ok": True, "_filas_afectadas": 42}

        with patch(
            "app.core.audit.audit_action",
            new_callable=AsyncMock,
        ) as mock_audit:
            await fake_endpoint(
                request=MagicMock(spec=Request),
                current_user=mock_user,
                db=MagicMock(spec=AsyncSession),
            )

        call_kwargs = mock_audit.await_args[1]
        assert call_kwargs["filas_afectadas"] == 42


class TestAuditedDecoratorFailure:
    """Scenario: endpoint decorado lanza excepción."""

    async def test_http_exception_does_not_call_audit_action(self) -> None:
        """WHEN endpoint decorado lanza HTTPException,
        THEN audit_action NO es llamada."""
        mock_user = MagicMock()
        mock_user.id = uuid.uuid4()
        mock_user.tenant_id = uuid.uuid4()

        @audited("TEST_ACCION")
        async def failing_endpoint(
            request: Request | None = None,
            current_user: object = None,
            db: AsyncSession | None = None,
            **kwargs: object,
        ) -> dict:
            msg = "bad request"
            raise HTTPException(status_code=400, detail=msg)

        with patch(
            "app.core.audit.audit_action",
            new_callable=AsyncMock,
        ) as mock_audit:
            with pytest.raises(HTTPException) as exc_info:
                await failing_endpoint(
                    request=MagicMock(spec=Request),
                    current_user=mock_user,
                    db=MagicMock(spec=AsyncSession),
                )

        assert exc_info.value.status_code == 400
        mock_audit.assert_not_awaited()

    async def test_unhandled_exception_does_not_call_audit_action(self) -> None:
        """WHEN endpoint decorado lanza excepción genérica,
        THEN audit_action NO es llamada."""
        mock_user = MagicMock()
        mock_user.id = uuid.uuid4()
        mock_user.tenant_id = uuid.uuid4()

        @audited("TEST_ACCION")
        async def failing_endpoint(
            request: Request | None = None,
            current_user: object = None,
            db: AsyncSession | None = None,
            **kwargs: object,
        ) -> dict:
            msg = "internal error"
            raise RuntimeError(msg)

        with patch(
            "app.core.audit.audit_action",
            new_callable=AsyncMock,
        ) as mock_audit:
            with pytest.raises(RuntimeError):
                await failing_endpoint(
                    request=MagicMock(spec=Request),
                    current_user=mock_user,
                    db=MagicMock(spec=AsyncSession),
                )

        mock_audit.assert_not_awaited()

    async def test_no_current_user_skips_audit(self) -> None:
        """WHEN current_user no está en kwargs,
        THEN NO se llama audit_action (no hay crash)."""
        @audited("TEST_ACCION")
        async def no_user_endpoint(
            request: Request | None = None,
            db: AsyncSession | None = None,
            **kwargs: object,
        ) -> dict:
            return {"ok": True}

        with patch(
            "app.core.audit.audit_action",
            new_callable=AsyncMock,
        ) as mock_audit:
            result = await no_user_endpoint(
                request=MagicMock(spec=Request),
                db=MagicMock(spec=AsyncSession),
            )

        assert result == {"ok": True}
        mock_audit.assert_not_awaited()


class TestAuditedDecoratorImpersonation:
    """Scenario: endpoint decorado bajo sesión de impersonación."""

    async def test_impersonated_sets_impersonado_id(self) -> None:
        """WHEN current_user tiene impersonated=True,
        THEN audit_action recibe impersonado_id = current_user.id
        y actor_id de current_user.actor_id."""
        admin_id = uuid.uuid4()
        impersonated_id = uuid.uuid4()
        tenant_id = uuid.uuid4()

        mock_user = MagicMock()
        mock_user.id = impersonated_id
        mock_user.tenant_id = tenant_id
        mock_user.actor_id = admin_id
        mock_user.impersonated = True

        @audited("IMPERSONACION_TEST")
        async def imp_endpoint(
            request: Request | None = None,
            current_user: object = None,
            db: AsyncSession | None = None,
            **kwargs: object,
        ) -> dict:
            return {"ok": True}

        with patch(
            "app.core.audit.audit_action",
            new_callable=AsyncMock,
        ) as mock_audit:
            await imp_endpoint(
                request=MagicMock(spec=Request),
                current_user=mock_user,
                db=MagicMock(spec=AsyncSession),
            )

        call_kwargs = mock_audit.await_args[1]
        ctx = call_kwargs["ctx"]
        assert ctx.actor_id == admin_id
        assert ctx.impersonado_id == impersonated_id


class TestAuditedDecoratorWithAuditCodes:
    """Scenario: @audited se usa con constantes de AuditCodes."""

    async def test_audited_with_audit_codes_constant(self) -> None:
        """WHEN se usa @audited(AuditCodes.IMPERSONACION_INICIAR),
        THEN la accion se pasa correctamente."""
        mock_user = MagicMock()
        mock_user.id = uuid.uuid4()
        mock_user.tenant_id = uuid.uuid4()
        mock_user.impersonated = False

        @audited(AuditCodes.IMPERSONACION_INICIAR)
        async def imp_start_endpoint(
            request: Request | None = None,
            current_user: object = None,
            db: AsyncSession | None = None,
            **kwargs: object,
        ) -> dict:
            return {"ok": True}

        with patch(
            "app.core.audit.audit_action",
            new_callable=AsyncMock,
        ) as mock_audit:
            await imp_start_endpoint(
                request=MagicMock(spec=Request),
                current_user=mock_user,
                db=MagicMock(spec=AsyncSession),
            )

        call_kwargs = mock_audit.await_args[1]
        assert call_kwargs["accion"] == AuditCodes.IMPERSONACION_INICIAR

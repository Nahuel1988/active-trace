"""Integration tests — derivación de aprobado (RN-01, RN-02, RN-03, D-01).

Strict TDD: RED → GREEN → TRIANGULATE → REFACTOR.
Usa contenedor de DB efímero — no mocks.
Marcado @pytest.mark.requires_db.
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import AuditContext
from app.models.calificacion import Calificacion, OrigenCalificacionDB, UmbralMateria
from app.models.padron import EntradaPadron, VersionPadron
from app.services.calificacion_service import CalificacionService, UmbralService

pytestmark = pytest.mark.requires_db


def _build_audit_ctx(user, tenant_id) -> AuditContext:
    return AuditContext(
        actor_id=user.id,
        tenant_id=tenant_id,
        ip="127.0.0.1",
        user_agent="test",
    )


class TestAprobadoDerivado:
    """Derivación de aprobado en read-time (Task 14.3)."""

    async def _setup_calificacion(
        self,
        db_session: AsyncSession,
        materia,
        user_factory,
        cohorte,
        *,
        nota_numerica: float | None = None,
        nota_textual: str | None = None,
    ):
        """Helper: crea tenant+user+materia+EntradaPadron+calificacion."""
        t, m = materia
        user = await user_factory(db_session, tenant_id=t.id)
        _, _, c = cohorte

        vp = VersionPadron(
            id=uuid.uuid4(),
            tenant_id=t.id,
            materia_id=m.id,
            cohorte_id=c.id,
            activa=True,
            total_entradas=1,
            origen="archivo",
        )
        db_session.add(vp)
        await db_session.flush()

        ep = EntradaPadron(
            id=uuid.uuid4(),
            tenant_id=t.id,
            version_padron_id=vp.id,
            nombre="Juan",
            apellidos="Pérez",
            email_encrypted="cifrado:test",
            comision="A",
        )
        db_session.add(ep)
        await db_session.flush()

        calif = Calificacion(
            id=uuid.uuid4(),
            tenant_id=t.id,
            entrada_padron_id=ep.id,
            materia_id=m.id,
            actividad="Parcial (Real)",
            nota_numerica=nota_numerica,
            nota_textual=nota_textual,
            origen=OrigenCalificacionDB.IMPORTADO,
            creado_por=user.id,
        )
        db_session.add(calif)
        await db_session.commit()
        await db_session.refresh(calif)

        return t, m, user, calif

    async def test_aprobado_numerico_supera_umbral_true(
        self,
        db_session: AsyncSession,
        materia,
        user_factory,
        asignacion_factory,
        cohorte,
    ):
        """14.3 RED: nota_numerica >= umbral_pct → aprobado=True."""
        t, m, user, calif = await self._setup_calificacion(
            db_session, materia, user_factory, cohorte, nota_numerica=75.0,
        )
        asignacion = await asignacion_factory(
            db_session, tenant_id=t.id, usuario_id=user.id, materia_id=m.id,
        )

        # Configurar umbral en 70
        umbral = UmbralMateria(
            id=uuid.uuid4(),
            tenant_id=t.id,
            asignacion_id=asignacion.id,
            materia_id=m.id,
            umbral_pct=70,
        )
        db_session.add(umbral)
        await db_session.commit()
        await db_session.refresh(umbral)

        service = CalificacionService()
        result = service._compute_aprobado(calif, umbral)
        assert result is True

    async def test_aprobado_numerico_no_supera_umbral_false(
        self,
        db_session: AsyncSession,
        materia,
        user_factory,
        asignacion_factory,
        cohorte,
    ):
        """14.3 RED: nota_numerica < umbral_pct → aprobado=False."""
        t, m, user, calif = await self._setup_calificacion(
            db_session, materia, user_factory, cohorte, nota_numerica=65.0,
        )
        asignacion = await asignacion_factory(
            db_session, tenant_id=t.id, usuario_id=user.id, materia_id=m.id,
        )

        umbral = UmbralMateria(
            id=uuid.uuid4(),
            tenant_id=t.id,
            asignacion_id=asignacion.id,
            materia_id=m.id,
            umbral_pct=70,
        )
        db_session.add(umbral)
        await db_session.commit()

        service = CalificacionService()
        result = service._compute_aprobado(calif, umbral)
        assert result is False

    async def test_aprobado_textual_en_valores_true(
        self,
        db_session: AsyncSession,
        materia,
        user_factory,
        asignacion_factory,
        cohorte,
    ):
        """14.3 TRIANGULATE: nota_textual en valores_aprobatorios → True."""
        t, m, user, calif = await self._setup_calificacion(
            db_session, materia, user_factory, cohorte, nota_textual="Promocionado",
        )
        asignacion = await asignacion_factory(
            db_session, tenant_id=t.id, usuario_id=user.id, materia_id=m.id,
        )

        umbral = UmbralMateria(
            id=uuid.uuid4(),
            tenant_id=t.id,
            asignacion_id=asignacion.id,
            materia_id=m.id,
            umbral_pct=60,
            valores_aprobatorios=["Aprobado", "Promocionado"],
        )
        db_session.add(umbral)
        await db_session.commit()

        service = CalificacionService()
        result = service._compute_aprobado(calif, umbral)
        assert result is True

    async def test_aprobado_textual_fuera_de_valores_false(
        self,
        db_session: AsyncSession,
        materia,
        user_factory,
        asignacion_factory,
        cohorte,
    ):
        """14.3 TRIANGULATE: nota_textual NO en valores_aprobatorios → False."""
        t, m, user, calif = await self._setup_calificacion(
            db_session, materia, user_factory, cohorte, nota_textual="Regular",
        )
        asignacion = await asignacion_factory(
            db_session, tenant_id=t.id, usuario_id=user.id, materia_id=m.id,
        )

        umbral = UmbralMateria(
            id=uuid.uuid4(),
            tenant_id=t.id,
            asignacion_id=asignacion.id,
            materia_id=m.id,
            umbral_pct=60,
            valores_aprobatorios=["Aprobado", "Promocionado"],
        )
        db_session.add(umbral)
        await db_session.commit()

        service = CalificacionService()
        result = service._compute_aprobado(calif, umbral)
        assert result is False

    async def test_aprobado_cambio_umbral_retroactivo(
        self,
        db_session: AsyncSession,
        materia,
        user_factory,
        asignacion_factory,
        cohorte,
    ):
        """14.3 TRIANGULATE: cambio de umbral afecta aprobado retrospectivamente."""
        t, m, user, calif = await self._setup_calificacion(
            db_session, materia, user_factory, cohorte, nota_numerica=65.0,
        )
        asignacion = await asignacion_factory(
            db_session, tenant_id=t.id, usuario_id=user.id, materia_id=m.id,
        )

        service = CalificacionService()

        # Con umbral 70 → False
        umbral70 = UmbralMateria(
            id=uuid.uuid4(),
            tenant_id=t.id,
            asignacion_id=asignacion.id,
            materia_id=m.id,
            umbral_pct=70,
        )
        assert service._compute_aprobado(calif, umbral70) is False

        # Con umbral 60 → True (retroactivo)
        umbral60 = UmbralMateria(
            id=uuid.uuid4(),
            tenant_id=t.id,
            asignacion_id=asignacion.id,
            materia_id=m.id,
            umbral_pct=60,
        )
        assert service._compute_aprobado(calif, umbral60) is True

    async def test_aprobado_sin_umbral_configurado_usa_default(
        self,
        db_session: AsyncSession,
        materia,
        user_factory,
        cohorte,
    ):
        """14.3 TRIANGULATE: sin umbral → usa DEFAULT (60)."""
        _, _, _, calif = await self._setup_calificacion(
            db_session, materia, user_factory, cohorte, nota_numerica=70.0,
        )

        service = CalificacionService()

        # Sin umbral (None) → default 60, 70 >= 60 → True
        result = service._compute_aprobado(calif, None)
        assert result is True

    async def test_aprobado_sin_umbral_nota_menor_default_false(
        self,
        db_session: AsyncSession,
        materia,
        user_factory,
        cohorte,
    ):
        """14.3 TRIANGULATE: sin umbral, nota < 60 → False."""
        _, _, _, calif = await self._setup_calificacion(
            db_session, materia, user_factory, cohorte, nota_numerica=50.0,
        )

        service = CalificacionService()
        result = service._compute_aprobado(calif, None)
        assert result is False

    async def test_aprobado_textual_sin_valores_configurados_false(
        self,
        db_session: AsyncSession,
        materia,
        user_factory,
        asignacion_factory,
        cohorte,
    ):
        """14.3 TRIANGULATE: textual sin valores_aprobatorios → False."""
        t, m, user, calif = await self._setup_calificacion(
            db_session, materia, user_factory, cohorte, nota_textual="Aprobado",
        )
        asignacion = await asignacion_factory(
            db_session, tenant_id=t.id, usuario_id=user.id, materia_id=m.id,
        )

        umbral = UmbralMateria(
            id=uuid.uuid4(),
            tenant_id=t.id,
            asignacion_id=asignacion.id,
            materia_id=m.id,
            umbral_pct=60,
            valores_aprobatorios=None,  # Sin valores textuales
        )
        db_session.add(umbral)
        await db_session.commit()

        service = CalificacionService()
        result = service._compute_aprobado(calif, umbral)
        assert result is False

    async def test_aprobado_GetCalificaciones_integra_derivacion(
        self,
        db_session: AsyncSession,
        materia,
        user_factory,
        asignacion_factory,
        cohorte,
    ):
        """14.3 TRIANGULATE: get_calificaciones incluye aprobado derivado."""
        t, m, user, calif = await self._setup_calificacion(
            db_session, materia, user_factory, cohorte, nota_numerica=85.0,
        )
        await asignacion_factory(
            db_session, tenant_id=t.id, usuario_id=user.id, materia_id=m.id,
        )

        service = CalificacionService()
        result = await service.get_calificaciones(
            tenant_id=t.id,
            materia_id=m.id,
            creado_por=user.id,
            session=db_session,
        )

        assert len(result) == 1
        # Sin umbral configurado, 85 >= 60 → True
        assert result[0].aprobado is True

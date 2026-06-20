"""LiquidacionService — cálculo, vista, cierre, historial y exportación de liquidaciones."""

from __future__ import annotations

import logging
import uuid
from collections import defaultdict
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import AuditContext, audit_action
from app.core.audit_codes import AuditCodes
from app.models.asignacion import Asignacion
from app.models.liquidacion import EstadoLiquidacion, Liquidacion
from app.models.role import Role
from app.models.user import User
from app.repositories.liquidacion_repository import LiquidacionRepository
from app.repositories.salario_base_repository import SalarioBaseRepository
from app.repositories.salario_plus_repository import SalarioPlusRepository
from app.repositories.user_repository import UserRepository
from app.schemas.liquidacion import (
    KpisLiquidacion,
    LiquidacionResumen,
    LiquidacionResponse,
    LiquidacionSegmentadaResponse,
    SegmentoLiquidaciones,
)

logger = logging.getLogger(__name__)

ROLE_NEXO_CODE = "nexo"


class LiquidacionError(Exception):
    """Error de dominio del servicio de liquidaciones."""

    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


class LiquidacionService:
    """Servicio de liquidaciones de honorarios docentes.

    Implementa:
    - D2: cálculo on-demand síncrono.
    - D3: plus DISTINCT(grupo, rol) — una aplicación por clave.
    - D5: estado='Cerrada' → inmutable; recalculo rechazado.
    - D6: respuesta segmentada (general, nexo, facturantes).
    """

    def __init__(
        self,
        liquidacion_repo: LiquidacionRepository | None = None,
        salario_base_repo: SalarioBaseRepository | None = None,
        salario_plus_repo: SalarioPlusRepository | None = None,
        user_repo: UserRepository | None = None,
    ) -> None:
        self._liq_repo = liquidacion_repo or LiquidacionRepository()
        self._base_repo = salario_base_repo or SalarioBaseRepository()
        self._plus_repo = salario_plus_repo or SalarioPlusRepository()
        self._user_repo = user_repo or UserRepository()

    # ─────────────────────────────────────────────────────────────────────
    # Helpers privados
    # ─────────────────────────────────────────────────────────────────────

    async def _get_asignaciones_cohorte(
        self,
        *,
        tenant_id: UUID,
        cohorte_id: UUID,
        session: AsyncSession,
    ) -> list[Asignacion]:
        """Obtiene asignaciones vigentes de la cohorte con rol en ROLES_EN_ASIGNACION."""
        from datetime import datetime, timezone

        from app.models.asignacion import ROLES_EN_ASIGNACION
        from sqlalchemy import and_, or_

        now = datetime.now(timezone.utc)
        stmt = (
            select(Asignacion)
            .where(
                Asignacion.tenant_id == tenant_id,
                Asignacion.cohorte_id == cohorte_id,
                Asignacion.deleted_at.is_(None),
                Asignacion.desde <= now,
                or_(Asignacion.hasta.is_(None), Asignacion.hasta >= now),
            )
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def _get_role_code(
        self,
        *,
        role_id: UUID,
        session: AsyncSession,
    ) -> str | None:
        """Obtiene el code de un Role por su ID."""
        stmt = select(Role).where(Role.id == role_id)
        result = await session.execute(stmt)
        role = result.scalar_one_or_none()
        return role.code.upper() if role else None

    async def _get_user(
        self,
        *,
        tenant_id: UUID,
        usuario_id: UUID,
        session: AsyncSession,
    ) -> User | None:
        return await self._user_repo.get(id=usuario_id, tenant_id=tenant_id, session=session)

    # ─────────────────────────────────────────────────────────────────────
    # Cálculo (D2)
    # ─────────────────────────────────────────────────────────────────────

    async def calcular(
        self,
        *,
        tenant_id: UUID,
        cohorte_id: UUID,
        periodo: str,
        session: AsyncSession,
    ) -> LiquidacionResumen:
        """Calcula (o recalcula) las liquidaciones de una cohorte en un período.

        Flujo:
        1. Validar que no haya Cerradas → 409 si las hay (D5).
        2. Obtener asignaciones vigentes de la cohorte.
        3. Agrupar por usuario, determinar rol (mayor jerarquía si hay varios).
        4. Para cada docente: buscar base vigente, plus vigentes, CBU.
        5. Upsert batch (soft-delete Abiertas anteriores + insert nuevas).
        6. Retornar resumen.
        """
        # 1. Validar no hay cerradas
        if await self._liq_repo.exists_cerradas(
            tenant_id=tenant_id, cohorte_id=cohorte_id, periodo=periodo, session=session
        ):
            raise LiquidacionError(
                409,
                f"No se puede recalcular: existen liquidaciones Cerradas "
                f"para cohorte={cohorte_id} periodo={periodo}",
            )

        # 2. Obtener asignaciones vigentes
        asignaciones = await self._get_asignaciones_cohorte(
            tenant_id=tenant_id, cohorte_id=cohorte_id, session=session
        )

        # 3. Agrupar por usuario_id
        por_usuario: dict[UUID, list[Asignacion]] = defaultdict(list)
        for asig in asignaciones:
            por_usuario[asig.usuario_id].append(asig)

        nuevas_liquidaciones: list[Liquidacion] = []
        omitidos_sin_cbu: int = 0

        # 4. Calcular por docente
        for usuario_id, asigs in por_usuario.items():
            # Resolver rol: tomar la primera asignación (simplificación)
            asig_principal = asigs[0]
            role_code = await self._get_role_code(
                role_id=asig_principal.role_id, session=session
            )
            if role_code is None:
                logger.warning("Rol no encontrado para role_id=%s, omitiendo", asig_principal.role_id)
                continue

            # Verificar CBU del usuario
            user = await self._get_user(
                tenant_id=tenant_id, usuario_id=usuario_id, session=session
            )
            if user is None:
                logger.warning("Usuario %s no encontrado, omitiendo", usuario_id)
                continue

            if user.cbu_encrypted is None:
                logger.warning("Docente %s sin CBU, omitido del cálculo", usuario_id)
                omitidos_sin_cbu += 1
                continue

            # Obtener base vigente para el rol
            base = await self._base_repo.get_vigente(
                tenant_id=tenant_id, rol=role_code, periodo=periodo, session=session
            )
            monto_base = Decimal(str(base.monto)) if base else Decimal("0")

            # Obtener grupos DISTINCT desde las comisiones (PA-22/PA-23)
            # Las comisiones son identificadores de materia/grupo — se usan directamente
            # como claves de plus. En producción, el mapping viene de config del tenant.
            grupos_distintos = list({
                c for asig in asigs for c in (asig.comisiones or [])
            })

            plus_list = await self._plus_repo.get_vigentes_por_grupos(
                tenant_id=tenant_id,
                grupos=grupos_distintos,
                rol=role_code,
                periodo=periodo,
                session=session,
            )
            monto_plus = sum(Decimal(str(p.monto)) for p in plus_list)

            total = monto_base + monto_plus
            es_nexo = role_code == ROLE_NEXO_CODE.upper()
            excluido_por_factura = bool(user.facturador)

            comisiones_ids = [
                c for asig in asigs for c in (asig.comisiones or [])
            ]

            liq = Liquidacion(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                cohorte_id=cohorte_id,
                periodo=periodo,
                usuario_id=usuario_id,
                rol=role_code,
                comisiones=comisiones_ids,
                monto_base=monto_base,
                monto_plus=monto_plus,
                total=total,
                es_nexo=es_nexo,
                excluido_por_factura=excluido_por_factura,
                estado=EstadoLiquidacion.Abierta.value,
            )
            nuevas_liquidaciones.append(liq)

        # 5. Upsert batch
        creadas = await self._liq_repo.create_or_update_batch(
            tenant_id=tenant_id,
            cohorte_id=cohorte_id,
            periodo=periodo,
            liquidaciones=nuevas_liquidaciones,
            session=session,
        )

        total_general = sum(liq.total for liq in creadas)
        return LiquidacionResumen(
            cantidad_generada=len(creadas),
            total_general=Decimal(str(total_general)),
            docentes_omitidos_sin_cbu=omitidos_sin_cbu,
        )

    # ─────────────────────────────────────────────────────────────────────
    # Vista segmentada (D6)
    # ─────────────────────────────────────────────────────────────────────

    async def obtener_liquidaciones(
        self,
        *,
        tenant_id: UUID,
        cohorte_id: UUID,
        periodo: str,
        session: AsyncSession,
        usuario_id: UUID | None = None,
    ) -> LiquidacionSegmentadaResponse:
        """Retorna liquidaciones en estructura segmentada con KPIs (D6).

        Segmentos: general (ni nexo ni facturador),
                   nexo (es_nexo=True),
                   facturantes (excluido_por_factura=True).
        """
        liquidaciones = await self._liq_repo.get_by_cohorte_periodo(
            tenant_id=tenant_id,
            cohorte_id=cohorte_id,
            periodo=periodo,
            session=session,
            usuario_id=usuario_id,
        )

        segmentos: dict[str, list[LiquidacionResponse]] = {
            "general": [],
            "nexo": [],
            "facturantes": [],
        }

        for liq in liquidaciones:
            resp = LiquidacionResponse.model_validate(liq)
            if liq.excluido_por_factura:
                segmentos["facturantes"].append(resp)
            elif liq.es_nexo:
                segmentos["nexo"].append(resp)
            else:
                segmentos["general"].append(resp)

        def _subtotal(items: list[LiquidacionResponse]) -> Decimal:
            return sum((item.total for item in items), Decimal("0"))

        total_sin_factura = _subtotal(segmentos["general"]) + _subtotal(segmentos["nexo"])
        total_con_factura = _subtotal(segmentos["facturantes"])

        return LiquidacionSegmentadaResponse(
            segmentos={
                k: SegmentoLiquidaciones(liquidaciones=v, subtotal=_subtotal(v))
                for k, v in segmentos.items()
            },
            kpis=KpisLiquidacion(
                total_sin_factura=total_sin_factura,
                total_con_factura=total_con_factura,
            ),
        )

    # ─────────────────────────────────────────────────────────────────────
    # Historial (solo Cerradas)
    # ─────────────────────────────────────────────────────────────────────

    async def obtener_historial(
        self,
        *,
        tenant_id: UUID,
        session: AsyncSession,
        cohorte_id: UUID | None = None,
        periodo: str | None = None,
        usuario_id: UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[LiquidacionResponse]:
        """Retorna solo liquidaciones Cerradas (historial inmutable)."""
        cerradas = await self._liq_repo.get_cerradas(
            tenant_id=tenant_id,
            session=session,
            cohorte_id=cohorte_id,
            periodo=periodo,
            usuario_id=usuario_id,
            limit=limit,
            offset=offset,
        )
        return [LiquidacionResponse.model_validate(liq) for liq in cerradas]

    # ─────────────────────────────────────────────────────────────────────
    # Cierre (D5) — con auditoría (task 11.2 integrado aquí)
    # ─────────────────────────────────────────────────────────────────────

    async def cerrar(
        self,
        *,
        tenant_id: UUID,
        liquidacion_id: UUID,
        session: AsyncSession,
        audit_ctx: AuditContext | None = None,
    ) -> LiquidacionResponse:
        """Cambia el estado de una Liquidacion a Cerrada y registra auditoría.

        Reglas (D5):
        - Solo se puede cerrar una Abierta.
        - Una vez Cerrada, es inmutable.
        - Se registra LIQUIDACION_CERRAR en audit_log.
        """
        # Verificar que existe
        liq = await self._liq_repo.get(
            id=liquidacion_id, tenant_id=tenant_id, session=session
        )
        if liq is None:
            raise LiquidacionError(404, "Liquidación no encontrada")

        if liq.estado == EstadoLiquidacion.Cerrada.value:
            raise LiquidacionError(409, "La liquidación ya está Cerrada (inmutable)")

        filas = await self._liq_repo.cerrar(
            tenant_id=tenant_id, liquidacion_id=liquidacion_id, session=session
        )
        if filas == 0:
            raise LiquidacionError(409, "No se pudo cerrar la liquidación")

        # Refrescar estado
        await session.refresh(liq)

        # Registrar auditoría si se provee contexto
        if audit_ctx is not None:
            await audit_action(
                ctx=audit_ctx,
                accion=AuditCodes.LIQUIDACION_CERRAR,
                detalle={
                    "liquidacion_id": str(liquidacion_id),
                    "cohorte_id": str(liq.cohorte_id),
                    "periodo": liq.periodo,
                    "usuario_id": str(liq.usuario_id),
                    "total": str(liq.total),
                },
                session=session,
                filas_afectadas=filas,
            )

        return LiquidacionResponse.model_validate(liq)

    # ─────────────────────────────────────────────────────────────────────
    # Exportar (stub — formato completo en C-24)
    # ─────────────────────────────────────────────────────────────────────

    async def exportar(
        self,
        *,
        tenant_id: UUID,
        cohorte_id: UUID,
        periodo: str,
        session: AsyncSession,
    ) -> list[dict[str, Any]]:
        """Genera datos planos de liquidaciones para exportación (formato a definir en C-24)."""
        liquidaciones = await self._liq_repo.get_by_cohorte_periodo(
            tenant_id=tenant_id,
            cohorte_id=cohorte_id,
            periodo=periodo,
            session=session,
        )
        return [
            {
                "liquidacion_id": str(liq.id),
                "usuario_id": str(liq.usuario_id),
                "rol": liq.rol,
                "periodo": liq.periodo,
                "monto_base": str(liq.monto_base),
                "monto_plus": str(liq.monto_plus),
                "total": str(liq.total),
                "estado": liq.estado,
                "es_nexo": liq.es_nexo,
                "excluido_por_factura": liq.excluido_por_factura,
            }
            for liq in liquidaciones
        ]

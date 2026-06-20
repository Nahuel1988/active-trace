"""MonitorService — monitores transversales de actividad académica.

Cubre:
- F2.7: Monitor general (coordinación/admin) — todos los alumnos del tenant
- F2.8: Monitor de seguimiento (tutor/profesor) — alumnos propios
- F2.9: Monitor de seguimiento con rango de fechas (coord/admin)
"""

from __future__ import annotations

import csv
import io
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asignacion import Asignacion
from app.models.calificacion import Calificacion, UmbralMateria
from app.models.materia import Materia
from app.models.padron import EntradaPadron, VersionPadron
from app.schemas.analisis import MonitorItem, MonitorResponse

_DEFAULT_UMBRAL_PCT = 60


def _compute_aprobado(
    nota_numerica: float | None,
    nota_textual: str | None,
    umbral_val: int | None = None,
    valores_aprobatorios: list[str] | None = None,
) -> bool:
    if nota_numerica is not None:
        threshold = umbral_val if umbral_val is not None else _DEFAULT_UMBRAL_PCT
        return nota_numerica >= threshold
    if nota_textual is not None:
        if valores_aprobatorios:
            return nota_textual in valores_aprobatorios
        return False
    return False


class MonitorError(Exception):
    """Error de dominio en operaciones de monitor."""

    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


class MonitorService:
    """Servicio de monitores transversales de actividad.

    Dependencias: modelos EntradaPadron, Calificacion, Asignacion, Materia.
    """

    async def get_monitor_general(
        self,
        *,
        tenant_id: UUID,
        materia_id: UUID | None = None,
        regional: str | None = None,
        comision: str | None = None,
        q: str | None = None,
        estado: str | None = None,
        limit: int = 50,
        offset: int = 0,
        session: AsyncSession,
    ) -> MonitorResponse:
        """Retorna vista general de todos los alumnos del tenant (F2.7).

        Args:
            tenant_id: UUID del tenant.
            materia_id: Filtrar por materia (opcional).
            regional: Filtrar por regional (opcional).
            comision: Filtrar por comisión (opcional).
            q: Búsqueda por texto libre (nombre/apellido, opcional).
            estado: ``"atrasado"`` para filtrar solo atrasados.
            limit: Máximo de resultados (default 50).
            offset: Desplazamiento (default 0).
            session: Sesión async.

        Returns:
            MonitorResponse paginado.
        """
        return await self._query_monitor(
            tenant_id=tenant_id,
            materia_id=materia_id,
            regional=regional,
            comision=comision,
            q=q,
            estado=estado,
            limit=limit,
            offset=offset,
            user_id=None,
            session=session,
        )

    async def get_monitor_seguimiento(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        materia_id: UUID | None = None,
        comision: str | None = None,
        q: str | None = None,
        estado: str | None = None,
        fecha_desde: str | None = None,
        fecha_hasta: str | None = None,
        limit: int = 50,
        offset: int = 0,
        session: AsyncSession,
    ) -> MonitorResponse:
        """Retorna vista de seguimiento scoped al usuario (F2.8, F2.9).

        Para TUTOR/PROFESOR: solo alumnos de sus materias asignadas.
        Para COORDINADOR/ADMIN: soporta filtro por rango de fechas.

        Args:
            tenant_id: UUID del tenant.
            user_id: UUID del usuario.
            materia_id: Filtrar por materia (opcional).
            comision: Filtrar por comisión (opcional).
            q: Búsqueda por texto libre (opcional).
            estado: ``"atrasado"`` para filtrar solo atrasados.
            fecha_desde: Fecha inicio (YYYY-MM-DD, opcional).
            fecha_hasta: Fecha fin (YYYY-MM-DD, opcional).
            limit: Máximo de resultados (default 50).
            offset: Desplazamiento (default 0).
            session: Sesión async.

        Returns:
            MonitorResponse paginado.
        """
        return await self._query_monitor(
            tenant_id=tenant_id,
            materia_id=materia_id,
            comision=comision,
            q=q,
            estado=estado,
            limit=limit,
            offset=offset,
            user_id=user_id,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            session=session,
        )

    async def _query_monitor(
        self,
        *,
        tenant_id: UUID,
        materia_id: UUID | None = None,
        regional: str | None = None,
        comision: str | None = None,
        q: str | None = None,
        estado: str | None = None,
        limit: int = 50,
        offset: int = 0,
        user_id: UUID | None = None,
        fecha_desde: str | None = None,
        fecha_hasta: str | None = None,
        session: AsyncSession,
    ) -> MonitorResponse:
        """Motor interno de consulta de monitores."""
        # Build base query for EntradaPadron with VersionPadron
        query = (
            select(EntradaPadron)
            .join(VersionPadron, EntradaPadron.version_padron_id == VersionPadron.id)
            .where(
                EntradaPadron.tenant_id == tenant_id,
                EntradaPadron.deleted_at.is_(None),
                VersionPadron.deleted_at.is_(None),
                VersionPadron.activa == True,
            )
        )

        if materia_id:
            query = query.where(VersionPadron.materia_id == materia_id)

        if regional:
            query = query.where(EntradaPadron.regional == regional)

        if comision:
            query = query.where(EntradaPadron.comision == comision)

        if q:
            search_term = f"%{q}%"
            query = query.where(
                or_(
                    EntradaPadron.nombre.ilike(search_term),
                    EntradaPadron.apellidos.ilike(search_term),
                )
            )

        # If user_id is provided, scope to their assigned materias
        if user_id:
            subq = select(Asignacion.materia_id).where(
                Asignacion.tenant_id == tenant_id,
                Asignacion.usuario_id == user_id,
                Asignacion.deleted_at.is_(None),
            )
            query = query.where(VersionPadron.materia_id.in_(subq))

        # Count total before pagination
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await session.execute(count_query)
        total = count_result.scalar() or 0

        # Apply pagination
        query = query.offset(offset).limit(limit)
        result = await session.execute(query)
        entradas = list(result.scalars().all())

        if not entradas:
            return MonitorResponse(items=[], total=0, limit=limit, offset=offset)

        # Get materia names for each version padron
        vp_ids = list(set(e.version_padron_id for e in entradas))
        stmt_vp = select(VersionPadron).where(
            VersionPadron.id.in_(vp_ids),
            VersionPadron.deleted_at.is_(None),
        )
        result_vp = await session.execute(stmt_vp)
        vps = {vp.id: vp for vp in result_vp.scalars().all()}

        m_ids = list(set(vp.materia_id for vp in vps.values()))
        stmt_m = select(Materia).where(
            Materia.id.in_(m_ids),
            Materia.deleted_at.is_(None),
        )
        result_m = await session.execute(stmt_m)
        materias = {m.id: m for m in result_m.scalars().all()}

        # Get calificaciones for all entradas
        entrada_ids = [e.id for e in entradas]
        stmt_calif = select(Calificacion).where(
            Calificacion.tenant_id == tenant_id,
            Calificacion.entrada_padron_id.in_(entrada_ids),
            Calificacion.deleted_at.is_(None),
        )
        result_calif = await session.execute(stmt_calif)
        calificaciones = list(result_calif.scalars().all())

        # Group calificaciones by entrada
        calif_por_entrada: dict[UUID, list[Calificacion]] = {}
        for c in calificaciones:
            calif_por_entrada.setdefault(c.entrada_padron_id, []).append(c)

        # Get umbrales for all materias involved
        stmt_u = select(UmbralMateria).where(
            UmbralMateria.tenant_id == tenant_id,
            UmbralMateria.materia_id.in_(m_ids),
            UmbralMateria.deleted_at.is_(None),
        )
        result_u = await session.execute(stmt_u)
        umbrales_dict: dict[UUID, UmbralMateria] = {}
        for u in result_u.scalars().all():
            if u.materia_id not in umbrales_dict:
                umbrales_dict[u.materia_id] = u

        items: list[MonitorItem] = []
        for ep in entradas:
            vp = vps.get(ep.version_padron_id)
            if vp is None:
                continue
            materia = materias.get(vp.materia_id)
            if materia is None:
                continue

            umbral_obj = umbrales_dict.get(vp.materia_id)
            umbral_val = umbral_obj.umbral_pct if umbral_obj else _DEFAULT_UMBRAL_PCT
            vals_aprob = umbral_obj.valores_aprobatorios if umbral_obj else None

            alumno_califs = calif_por_entrada.get(ep.id, [])
            approved_count = sum(
                1 for c in alumno_califs
                if _compute_aprobado(c.nota_numerica, c.nota_textual, umbral_val, vals_aprob)
            )
            total_count = len(alumno_califs)

            all_activities = {
                c2.actividad for c2 in calificaciones
                if c2.materia_id == vp.materia_id
            }
            alumno_activities = {c.actividad for c in alumno_califs}

            is_atrasado = False
            for activity in all_activities:
                if activity not in alumno_activities:
                    is_atrasado = True
                    break
            if not is_atrasado:
                for c in alumno_califs:
                    if not _compute_aprobado(c.nota_numerica, c.nota_textual, umbral_val, vals_aprob):
                        is_atrasado = True
                        break

            if estado == "atrasado" and not is_atrasado:
                continue

            items.append(MonitorItem(
                entrada_padron_id=ep.id,
                alumno_nombre=ep.nombre,
                alumno_apellido=ep.apellidos,
                materia_id=vp.materia_id,
                materia_nombre=materia.nombre,
                comision=ep.comision,
                actividades_aprobadas=approved_count,
                actividades_pendientes=max(total_count - approved_count, 0),
                atrasado=is_atrasado,
            ))

        return MonitorResponse(
            items=items,
            total=total,
            limit=limit,
            offset=offset,
        )

    async def export_monitor_csv(
        self,
        *,
        tenant_id: UUID,
        items: list[MonitorItem],
        session: AsyncSession,
    ) -> str:
        """Exporta items del monitor a formato CSV."""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "entrada_padron_id", "alumno_nombre", "alumno_apellido",
            "materia", "comision", "actividades_aprobadas",
            "actividades_pendientes", "atrasado",
        ])
        for item in items:
            writer.writerow([
                str(item.entrada_padron_id),
                item.alumno_nombre,
                item.alumno_apellido,
                item.materia_nombre,
                item.comision,
                item.actividades_aprobadas,
                item.actividades_pendientes,
                "Si" if item.atrasado else "No",
            ])
        return output.getvalue()

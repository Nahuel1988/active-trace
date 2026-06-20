"""AnalisisService — atrasados, ranking, reportes rápidos, notas finales, entregas pendientes.

Reglas de negocio cubiertas:
- RN-03: umbral_pct default = 60
- RN-06: detección de alumnos atrasados por materia×cohorte
- RN-07: cruce con reporte de finalización para identificar actividades sin corregir
- RN-08: SOLO actividades textuales en reporte de entregas pendientes
- RN-09: ranking descendente de actividades aprobadas
"""

from __future__ import annotations

import csv
import io
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.calificacion import Calificacion, UmbralMateria
from app.models.materia import Materia
from app.models.padron import EntradaPadron, VersionPadron
from app.schemas.analisis import (
    AtrasadoItem,
    AtrasadosResponse,
    EntregaPendienteItem,
    EntregasPendientesResponse,
    NotaActividad,
    NotaFinalAlumno,
    NotasFinalesResponse,
    RankingItem,
    RankingResponse,
    ReporteRapidoResponse,
)

_DEFAULT_UMBRAL_PCT = 60


def _compute_aprobado(
    nota_numerica: float | None,
    nota_textual: str | None,
    umbral: UmbralMateria | None,
) -> bool:
    """Determina si una calificación está aprobada dado el umbral."""
    if umbral is not None and umbral.deleted_at is not None:
        umbral = None

    if nota_numerica is not None:
        threshold = umbral.umbral_pct if umbral else _DEFAULT_UMBRAL_PCT
        return nota_numerica >= threshold

    if nota_textual is not None:
        if umbral and umbral.valores_aprobatorios:
            return nota_textual in umbral.valores_aprobatorios
        return False

    return False


class AnalisisError(Exception):
    """Error de dominio en operaciones de análisis."""

    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


class AnalisisService:
    """Servicio de análisis académico.

    Dependencias: modelos Calificacion, UmbralMateria, Materia, EntradaPadron,
    VersionPadron.
    """

    async def _get_version_padron(
        self,
        *,
        tenant_id: UUID,
        materia_id: UUID,
        cohorte_id: UUID | None,
        session: AsyncSession,
    ) -> VersionPadron | None:
        stmt = select(VersionPadron).where(
            VersionPadron.tenant_id == tenant_id,
            VersionPadron.materia_id == materia_id,
            VersionPadron.deleted_at.is_(None),
            VersionPadron.activa == True,
        )
        if cohorte_id:
            stmt = stmt.where(VersionPadron.cohorte_id == cohorte_id)
        stmt = stmt.limit(1)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_entradas(
        self,
        *,
        tenant_id: UUID,
        version_padron_id: UUID,
        session: AsyncSession,
    ) -> list[EntradaPadron]:
        stmt = select(EntradaPadron).where(
            EntradaPadron.tenant_id == tenant_id,
            EntradaPadron.version_padron_id == version_padron_id,
            EntradaPadron.deleted_at.is_(None),
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def _get_umbral_materia(
        self,
        *,
        tenant_id: UUID,
        materia_id: UUID,
        session: AsyncSession,
    ) -> UmbralMateria | None:
        stmt = select(UmbralMateria).where(
            UmbralMateria.tenant_id == tenant_id,
            UmbralMateria.materia_id == materia_id,
            UmbralMateria.deleted_at.is_(None),
        ).limit(1)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_calificaciones_por_entradas(
        self,
        *,
        tenant_id: UUID,
        materia_id: UUID,
        entrada_ids: list[UUID],
        session: AsyncSession,
    ) -> list[Calificacion]:
        if not entrada_ids:
            return []
        stmt = select(Calificacion).where(
            Calificacion.tenant_id == tenant_id,
            Calificacion.materia_id == materia_id,
            Calificacion.entrada_padron_id.in_(entrada_ids),
            Calificacion.deleted_at.is_(None),
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def get_atrasados(
        self,
        *,
        tenant_id: UUID,
        materia_id: UUID,
        cohorte_id: UUID | None = None,
        session: AsyncSession,
    ) -> AtrasadosResponse:
        """Computa alumnos atrasados para una materia×cohorte.

        Clasifica cada estudiante como:
        - ``missing``: actividad sin entrega (sin calificación)
        - ``below_threshold``: nota por debajo del umbral

        Args:
            tenant_id: UUID del tenant.
            materia_id: UUID de la materia.
            cohorte_id: UUID de la cohorte (opcional).
            session: Sesión async.

        Returns:
            AtrasadosResponse con items clasificados.
        """
        stmt_m = select(Materia).where(
            Materia.tenant_id == tenant_id,
            Materia.id == materia_id,
            Materia.deleted_at.is_(None),
        )
        result_m = await session.execute(stmt_m)
        materia = result_m.scalar_one_or_none()
        if materia is None:
            return AtrasadosResponse(items=[], total=0)

        vp = await self._get_version_padron(
            tenant_id=tenant_id, materia_id=materia_id, cohorte_id=cohorte_id,
            session=session,
        )
        if vp is None:
            return AtrasadosResponse(items=[], total=0)

        entradas = await self._get_entradas(
            tenant_id=tenant_id, version_padron_id=vp.id, session=session,
        )
        if not entradas:
            return AtrasadosResponse(items=[], total=0)

        entrada_ids = [e.id for e in entradas]
        entrada_map = {e.id: e for e in entradas}

        calificaciones = await self._get_calificaciones_por_entradas(
            tenant_id=tenant_id, materia_id=materia_id,
            entrada_ids=entrada_ids, session=session,
        )
        umbral = await self._get_umbral_materia(
            tenant_id=tenant_id, materia_id=materia_id, session=session,
        )

        calif_por_entrada: dict[UUID, list[Calificacion]] = {}
        for c in calificaciones:
            calif_por_entrada.setdefault(c.entrada_padron_id, []).append(c)

        all_activities = {c.actividad for c in calificaciones}

        items: list[AtrasadoItem] = []
        for ep in entradas:
            alumno_califs = calif_por_entrada.get(ep.id, [])
            alumno_activities = {c.actividad for c in alumno_califs}

            for activity in all_activities:
                if activity not in alumno_activities:
                    items.append(AtrasadoItem(
                        entrada_padron_id=ep.id,
                        alumno_nombre=ep.nombre,
                        alumno_apellido=ep.apellidos,
                        materia_id=materia_id,
                        materia_nombre=materia.nombre,
                        clasificacion="missing",
                        actividad=activity,
                    ))

            for c in alumno_califs:
                aprobado = _compute_aprobado(
                    c.nota_numerica, c.nota_textual, umbral,
                )
                if not aprobado:
                    items.append(AtrasadoItem(
                        entrada_padron_id=ep.id,
                        alumno_nombre=ep.nombre,
                        alumno_apellido=ep.apellidos,
                        materia_id=materia_id,
                        materia_nombre=materia.nombre,
                        clasificacion="below_threshold",
                        actividad=c.actividad,
                    ))

        return AtrasadosResponse(items=items, total=len(items))

    async def get_ranking(
        self,
        *,
        tenant_id: UUID,
        materia_id: UUID,
        cohorte_id: UUID | None = None,
        session: AsyncSession,
    ) -> RankingResponse:
        """Computa ranking descendente de actividades aprobadas por alumno.

        RN-09: excluye alumnos sin actividades aprobadas.
        Tie-breaking: alfabético por apellido, luego nombre.

        Args:
            tenant_id: UUID del tenant.
            materia_id: UUID de la materia.
            cohorte_id: UUID de la cohorte (opcional).
            session: Sesión async.

        Returns:
            RankingResponse con items ordenados.
        """
        stmt_m = select(Materia).where(
            Materia.tenant_id == tenant_id,
            Materia.id == materia_id,
            Materia.deleted_at.is_(None),
        )
        result_m = await session.execute(stmt_m)
        materia = result_m.scalar_one_or_none()
        if materia is None:
            return RankingResponse(items=[])

        vp = await self._get_version_padron(
            tenant_id=tenant_id, materia_id=materia_id, cohorte_id=cohorte_id,
            session=session,
        )
        if vp is None:
            return RankingResponse(items=[])

        entradas = await self._get_entradas(
            tenant_id=tenant_id, version_padron_id=vp.id, session=session,
        )
        if not entradas:
            return RankingResponse(items=[])

        entrada_ids = [e.id for e in entradas]
        entrada_map = {e.id: e for e in entradas}

        calificaciones = await self._get_calificaciones_por_entradas(
            tenant_id=tenant_id, materia_id=materia_id,
            entrada_ids=entrada_ids, session=session,
        )
        umbral = await self._get_umbral_materia(
            tenant_id=tenant_id, materia_id=materia_id, session=session,
        )

        calif_por_entrada: dict[UUID, list[Calificacion]] = {}
        for c in calificaciones:
            calif_por_entrada.setdefault(c.entrada_padron_id, []).append(c)

        all_activities = {c.actividad for c in calificaciones}
        total_activities = len(all_activities)

        items: list[RankingItem] = []
        for ep in entradas:
            alumno_califs = calif_por_entrada.get(ep.id, [])
            approved_count = sum(
                1 for c in alumno_califs
                if _compute_aprobado(c.nota_numerica, c.nota_textual, umbral)
            )
            if approved_count == 0:
                continue

            items.append(RankingItem(
                entrada_padron_id=ep.id,
                alumno_nombre=ep.nombre,
                alumno_apellido=ep.apellidos,
                actividades_aprobadas=approved_count,
                total_actividades=max(total_activities, len(alumno_califs)),
                porcentaje_aprobacion=round(
                    (approved_count / max(total_activities, 1)) * 100, 2
                ),
            ))

        items.sort(key=lambda x: (
            -x.actividades_aprobadas, x.alumno_apellido, x.alumno_nombre,
        ))

        return RankingResponse(items=items)

    async def get_reporte_rapido(
        self,
        *,
        tenant_id: UUID,
        materia_id: UUID,
        cohorte_id: UUID | None = None,
        session: AsyncSession,
    ) -> ReporteRapidoResponse:
        """Computa métricas rápidas agregadas para una materia×cohorte.

        Args:
            tenant_id: UUID del tenant.
            materia_id: UUID de la materia.
            cohorte_id: UUID de la cohorte (opcional).
            session: Sesión async.

        Returns:
            ReporteRapidoResponse con métricas.
        """
        vp = await self._get_version_padron(
            tenant_id=tenant_id, materia_id=materia_id, cohorte_id=cohorte_id,
            session=session,
        )
        if vp is None:
            return ReporteRapidoResponse(
                total_alumnos=0, total_actividades=0,
                tasa_aprobacion_pct=0.0, alumnos_atrasados=0,
                alumnos_al_dia=0, sin_datos=True,
            )

        entradas = await self._get_entradas(
            tenant_id=tenant_id, version_padron_id=vp.id, session=session,
        )
        if not entradas:
            return ReporteRapidoResponse(
                total_alumnos=0, total_actividades=0,
                tasa_aprobacion_pct=0.0, alumnos_atrasados=0,
                alumnos_al_dia=0, sin_datos=True,
            )

        entrada_ids = [e.id for e in entradas]

        calificaciones = await self._get_calificaciones_por_entradas(
            tenant_id=tenant_id, materia_id=materia_id,
            entrada_ids=entrada_ids, session=session,
        )

        if not calificaciones:
            return ReporteRapidoResponse(
                total_alumnos=len(entradas), total_actividades=0,
                tasa_aprobacion_pct=0.0, alumnos_atrasados=0,
                alumnos_al_dia=0, sin_datos=True,
            )

        umbral = await self._get_umbral_materia(
            tenant_id=tenant_id, materia_id=materia_id, session=session,
        )

        all_activities = {c.actividad for c in calificaciones}
        total_approved = sum(
            1 for c in calificaciones
            if _compute_aprobado(c.nota_numerica, c.nota_textual, umbral)
        )

        calif_por_entrada: dict[UUID, list[Calificacion]] = {}
        for c in calificaciones:
            calif_por_entrada.setdefault(c.entrada_padron_id, []).append(c)

        atrasados_count = 0
        for ep in entradas:
            alumno_califs = calif_por_entrada.get(ep.id, [])
            alumno_activities = {c.actividad for c in alumno_califs}

            is_atrasado = False
            for activity in all_activities:
                if activity not in alumno_activities:
                    is_atrasado = True
                    break

            if not is_atrasado:
                for c in alumno_califs:
                    if not _compute_aprobado(c.nota_numerica, c.nota_textual, umbral):
                        is_atrasado = True
                        break

            if is_atrasado:
                atrasados_count += 1

        total_grades = len(calificaciones)
        tasa = round((total_approved / total_grades) * 100, 2) if total_grades else 0.0

        return ReporteRapidoResponse(
            total_alumnos=len(entradas),
            total_actividades=len(all_activities),
            tasa_aprobacion_pct=tasa,
            alumnos_atrasados=atrasados_count,
            alumnos_al_dia=len(entradas) - atrasados_count,
        )

    async def get_notas_finales(
        self,
        *,
        tenant_id: UUID,
        materia_id: UUID,
        cohorte_id: UUID | None = None,
        format: str = "json",
        session: AsyncSession,
    ) -> NotasFinalesResponse | str:
        """Computa notas finales agrupadas por alumno.

        Solo actividades numéricas se promedian. Actividades textuales se
        listan por separado sin afectar el promedio.

        Args:
            tenant_id: UUID del tenant.
            materia_id: UUID de la materia.
            cohorte_id: UUID de la cohorte (opcional).
            format: ``"json"`` (default) o ``"csv"``.
            session: Sesión async.

        Returns:
            NotasFinalesResponse (json) o string CSV.
        """
        stmt_m = select(Materia).where(
            Materia.tenant_id == tenant_id,
            Materia.id == materia_id,
            Materia.deleted_at.is_(None),
        )
        result_m = await session.execute(stmt_m)
        materia = result_m.scalar_one_or_none()
        if materia is None:
            return NotasFinalesResponse(items=[])

        vp = await self._get_version_padron(
            tenant_id=tenant_id, materia_id=materia_id, cohorte_id=cohorte_id,
            session=session,
        )
        if vp is None:
            return NotasFinalesResponse(items=[])

        entradas = await self._get_entradas(
            tenant_id=tenant_id, version_padron_id=vp.id, session=session,
        )
        if not entradas:
            return NotasFinalesResponse(items=[])

        entrada_ids = [e.id for e in entradas]
        entrada_map = {e.id: e for e in entradas}

        calificaciones = await self._get_calificaciones_por_entradas(
            tenant_id=tenant_id, materia_id=materia_id,
            entrada_ids=entrada_ids, session=session,
        )
        umbral = await self._get_umbral_materia(
            tenant_id=tenant_id, materia_id=materia_id, session=session,
        )

        calif_por_entrada: dict[UUID, list[Calificacion]] = {}
        for c in calificaciones:
            calif_por_entrada.setdefault(c.entrada_padron_id, []).append(c)

        items: list[NotaFinalAlumno] = []
        for ep in entradas:
            alumno_califs = calif_por_entrada.get(ep.id, [])

            actividades = []
            actividades_textuales = []
            notas_numericas = []

            for c in alumno_califs:
                aprobado = _compute_aprobado(
                    c.nota_numerica, c.nota_textual, umbral,
                )
                nota = NotaActividad(
                    actividad=c.actividad,
                    nota_numerica=c.nota_numerica,
                    nota_textual=c.nota_textual,
                    aprobado=aprobado,
                )
                if c.nota_numerica is not None:
                    actividades.append(nota)
                    notas_numericas.append(c.nota_numerica)
                else:
                    actividades_textuales.append(nota)

            promedio = (
                round(sum(notas_numericas) / len(notas_numericas), 2)
                if notas_numericas else None
            )

            items.append(NotaFinalAlumno(
                entrada_padron_id=ep.id,
                alumno_nombre=ep.nombre,
                alumno_apellido=ep.apellidos,
                actividades=actividades,
                promedio_numerico=promedio,
                actividades_textuales=actividades_textuales,
            ))

        if format == "csv":
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow([
                "entrada_padron_id", "alumno_nombre", "alumno_apellido",
                "actividad", "nota_numerica", "nota_textual",
                "aprobado", "promedio_numerico",
            ])
            for alumno in items:
                for act in alumno.actividades + alumno.actividades_textuales:
                    writer.writerow([
                        str(alumno.entrada_padron_id),
                        alumno.alumno_nombre,
                        alumno.alumno_apellido,
                        act.actividad,
                        act.nota_numerica or "",
                        act.nota_textual or "",
                        "Si" if act.aprobado else "No",
                        alumno.promedio_numerico or "",
                    ])
            return output.getvalue()

        return NotasFinalesResponse(items=items)

    async def get_entregas_pendientes(
        self,
        *,
        tenant_id: UUID,
        materia_id: UUID,
        cohorte_id: UUID | None = None,
        session: AsyncSession,
    ) -> EntregasPendientesResponse:
        """Detecta actividades textuales sin calificar (RN-07, RN-08).

        Identifica actividades de escala textual que no tienen registro
        en Calificacion para cada alumno de la materia×cohorte.

        Args:
            tenant_id: UUID del tenant.
            materia_id: UUID de la materia.
            cohorte_id: UUID de la cohorte (opcional).
            session: Sesión async.

        Returns:
            EntregasPendientesResponse con items pendientes.
        """
        stmt_m = select(Materia).where(
            Materia.tenant_id == tenant_id,
            Materia.id == materia_id,
            Materia.deleted_at.is_(None),
        )
        result_m = await session.execute(stmt_m)
        materia = result_m.scalar_one_or_none()
        if materia is None:
            return EntregasPendientesResponse(items=[], todas_corregidas=True)

        vp = await self._get_version_padron(
            tenant_id=tenant_id, materia_id=materia_id, cohorte_id=cohorte_id,
            session=session,
        )
        if vp is None:
            return EntregasPendientesResponse(items=[], todas_corregidas=True)

        entradas = await self._get_entradas(
            tenant_id=tenant_id, version_padron_id=vp.id, session=session,
        )
        if not entradas:
            return EntregasPendientesResponse(items=[], todas_corregidas=True)

        entrada_ids = [e.id for e in entradas]
        entrada_map = {e.id: e for e in entradas}

        calificaciones = await self._get_calificaciones_por_entradas(
            tenant_id=tenant_id, materia_id=materia_id,
            entrada_ids=entrada_ids, session=session,
        )

        existing: dict[UUID, set[str]] = {}
        for c in calificaciones:
            existing.setdefault(c.entrada_padron_id, set()).add(c.actividad)

        textual_activities: set[str] = set()
        for c in calificaciones:
            if c.nota_numerica is None and c.nota_textual is not None:
                textual_activities.add(c.actividad)

        items: list[EntregaPendienteItem] = []
        for ep in entradas:
            alumno_existing = existing.get(ep.id, set())
            for act in sorted(textual_activities):
                if act not in alumno_existing:
                    items.append(EntregaPendienteItem(
                        alumno=f"{ep.nombre} {ep.apellidos}",
                        actividad=act,
                        fecha_submission="",
                        materia=materia.nombre,
                    ))

        return EntregasPendientesResponse(
            items=items,
            todas_corregidas=len(items) == 0,
        )

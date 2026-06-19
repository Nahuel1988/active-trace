"""EquipoService — operaciones de bloque sobre asignaciones como equipo docente.

Opera sobre Asignacion agrupadas por tupla (materia_id, carrera_id, cohorte_id).
Reutiliza AsignacionRepository y AsignacionService para validaciones.
"""

from __future__ import annotations

import csv
import io
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asignacion import Asignacion
from app.models.audit_log import AuditLog
from app.repositories.asignacion_repository import AsignacionRepository
from app.repositories.audit_log_repository import AuditLogRepository
from app.utils.csv_utils import escape_csv


class EquipoService:
    """Servicio de operaciones de bloque sobre equipos docentes.

    Dependencias:
        - AsignacionRepository: acceso a datos de asignación.
        - AsignacionService: validación por fila en creación.
        - AuditLogRepository: registro de auditoría.
    """

    def __init__(
        self,
        asignacion_repo: AsignacionRepository | None = None,
        audit_repo: AuditLogRepository | None = None,
    ) -> None:
        from app.services.asignacion_service import AsignacionService

        self._repo = asignacion_repo or AsignacionRepository()
        self._audit_repo = audit_repo or AuditLogRepository()
        self._asignacion_service = AsignacionService(
            asignacion_repo=self._repo,
            audit_repo=self._audit_repo,
        )

    # ── 3. Mis equipos ────────────────────────────────────────────────

    async def get_mis_equipos(
        self,
        *,
        tenant_id: UUID,
        usuario_id: UUID,
        session: AsyncSession,
    ) -> List[Dict[str, Any]]:
        """Asignaciones vigentes del usuario agrupadas por tupla de equipo.

        La identidad viene del JWT, nunca por parámetro.
        """
        asignaciones = await self._repo.list(
            tenant_id=tenant_id,
            estado_vigencia="vigente",
            usuario_id=usuario_id,
            session=session,
        )

        grupos: Dict[Tuple[Optional[str], Optional[str], Optional[str]], List[Asignacion]] = {}
        for a in asignaciones:
            key = (
                str(a.materia_id) if a.materia_id else None,
                str(a.carrera_id) if a.carrera_id else None,
                str(a.cohorte_id) if a.cohorte_id else None,
            )
            if key not in grupos:
                grupos[key] = []
            grupos[key].append(a)

        from app.repositories.usuario_repository import UsuarioRepository

        user_repo = UsuarioRepository()
        user = await user_repo.get(id=usuario_id, tenant_id=tenant_id, session=session)

        result = []
        for (mat, car, coh), items in grupos.items():
            equipo_items = []
            for a in items:
                equipo_items.append({
                    "id": str(a.id),
                    "role_id": str(a.role_id),
                    "comisiones": a.comisiones or [],
                    "responsable_id": str(a.responsable_id) if a.responsable_id else None,
                    "desde": a.desde,
                    "hasta": a.hasta,
                    "estado_vigencia": a.estado_vigencia,
                    "usuario_id": str(a.usuario_id),
                    "usuario_nombre": user.nombre if user else None,
                    "usuario_apellidos": user.apellidos if user else None,
                    "usuario_legajo": user.legajo if user else None,
                })
            result.append({
                "materia_id": mat,
                "carrera_id": car,
                "cohorte_id": coh,
                "asignaciones": equipo_items,
            })
        return result

    # ── 4. Asignación masiva (best-effort) ────────────────────────────

    async def asignacion_masiva(
        self,
        *,
        tenant_id: UUID,
        actor_id: UUID,
        role_id: UUID,
        role_code: str,
        usuario_ids: List[UUID],
        materia_id: Optional[UUID] = None,
        carrera_id: Optional[UUID] = None,
        cohorte_id: Optional[UUID] = None,
        comisiones: Optional[List[str]] = None,
        responsable_id: Optional[UUID] = None,
        desde: datetime,
        hasta: Optional[datetime] = None,
        session: AsyncSession,
        ip: str = "0.0.0.0",
        user_agent: str = "service",
    ) -> Dict[str, Any]:
        """Asignación masiva best-effort.

        Crea asignaciones para múltiples usuarios.
        Válidas se crean; inválidas se reportan; existentes se omiten.
        """
        creadas = 0
        rechazadas: List[Dict[str, str]] = []
        omitidas: List[Dict[str, str]] = []

        for uid in usuario_ids:
            existe = await self._repo.exists_vigente(
                tenant_id=tenant_id,
                usuario_id=uid,
                role_id=role_id,
                materia_id=materia_id,
                carrera_id=carrera_id,
                cohorte_id=cohorte_id,
                session=session,
            )
            if existe:
                omitidas.append({
                    "usuario_id": str(uid),
                    "motivo": "ya existe una asignación vigente para este usuario, rol y contexto",
                })
                continue

            try:
                await self._asignacion_service.create(
                    tenant_id=tenant_id,
                    actor_id=actor_id,
                    usuario_id=uid,
                    role_id=role_id,
                    role_code=role_code,
                    desde=desde,
                    hasta=hasta,
                    materia_id=materia_id,
                    carrera_id=carrera_id,
                    cohorte_id=cohorte_id,
                    responsable_id=responsable_id,
                    comisiones=comisiones or [],
                    session=session,
                )
                creadas += 1
            except Exception as exc:
                rechazadas.append({
                    "usuario_id": str(uid),
                    "motivo": str(exc),
                })

        await self._audit_repo.add(
            entry=AuditLog(
                tenant_id=tenant_id,
                actor_id=actor_id,
                accion="ASIGNACION_MODIFICAR",
                detalle={
                    "tipo": "asignacion_masiva",
                    "role_id": str(role_id),
                    "role_code": role_code,
                    "materia_id": str(materia_id) if materia_id else None,
                    "carrera_id": str(carrera_id) if carrera_id else None,
                    "cohorte_id": str(cohorte_id) if cohorte_id else None,
                    "rechazadas": len(rechazadas),
                    "omitidas": len(omitidas),
                },
                filas_afectadas=creadas,
                ip=ip,
                user_agent=user_agent,
            ),
            session=session,
        )
        return {"creadas": creadas, "rechazadas": rechazadas, "omitidas": omitidas}

    # ── 5. Clonar equipo (RN-12) ─────────────────────────────────────

    async def clonar_equipo(
        self,
        *,
        tenant_id: UUID,
        actor_id: UUID,
        origen_materia_id: UUID,
        origen_carrera_id: UUID,
        origen_cohorte_id: UUID,
        destino_carrera_id: UUID,
        destino_cohorte_id: UUID,
        destino_materia_id: Optional[UUID] = None,
        nuevo_desde: datetime,
        nuevo_hasta: Optional[datetime] = None,
        session: AsyncSession,
        ip: str = "0.0.0.0",
        user_agent: str = "service",
    ) -> Dict[str, Any]:
        """Clona asignaciones vigentes de origen a destino.

        Solo vigentes. Re-escribe carrera/cohorte/vigencia.
        No duplica si ya existe vigente en destino.
        """
        origen = await self._repo.list_by_equipo(
            tenant_id=tenant_id,
            materia_id=origen_materia_id,
            carrera_id=origen_carrera_id,
            cohorte_id=origen_cohorte_id,
            session=session,
            solo_vigentes=True,
        )

        materia_dest = destino_materia_id or origen_materia_id

        from app.models.role import Role
        from sqlalchemy import select

        role_ids = {str(a.role_id) for a in origen}
        roles_map: Dict[str, str] = {}
        if role_ids:
            stmt = select(Role).where(
                Role.id.in_([UUID(rid) for rid in role_ids]),
                Role.tenant_id == tenant_id,
                Role.deleted_at.is_(None),
            )
            result = await session.execute(stmt)
            for r in result.scalars().all():
                roles_map[str(r.id)] = r.code

        clonadas = 0
        omitidas: List[Dict[str, str]] = []

        for asig in origen:
            uid = asig.usuario_id
            role_id = asig.role_id
            role_code = roles_map.get(str(role_id), "")
            comisiones = asig.comisiones or []
            responsable_id = asig.responsable_id

            existe = await self._repo.exists_vigente(
                tenant_id=tenant_id,
                usuario_id=uid,
                role_id=role_id,
                materia_id=materia_dest,
                carrera_id=destino_carrera_id,
                cohorte_id=destino_cohorte_id,
                session=session,
            )
            if existe:
                omitidas.append({
                    "usuario_id": str(uid),
                    "motivo": "ya existe una asignación vigente en el destino",
                })
                continue

            try:
                await self._asignacion_service.create(
                    tenant_id=tenant_id,
                    actor_id=actor_id,
                    usuario_id=uid,
                    role_id=role_id,
                    role_code=role_code,
                    desde=nuevo_desde,
                    hasta=nuevo_hasta,
                    materia_id=materia_dest,
                    carrera_id=destino_carrera_id,
                    cohorte_id=destino_cohorte_id,
                    responsable_id=responsable_id,
                    comisiones=comisiones,
                    session=session,
                )
                clonadas += 1
            except Exception as exc:
                omitidas.append({
                    "usuario_id": str(uid),
                    "motivo": f"error al clonar: {exc!s}",
                })

        await self._audit_repo.add(
            entry=AuditLog(
                tenant_id=tenant_id,
                actor_id=actor_id,
                accion="ASIGNACION_MODIFICAR",
                detalle={
                    "tipo": "clonar_equipo",
                    "origen": {
                        "materia_id": str(origen_materia_id),
                        "carrera_id": str(origen_carrera_id),
                        "cohorte_id": str(origen_cohorte_id),
                    },
                    "destino": {
                        "materia_id": str(materia_dest),
                        "carrera_id": str(destino_carrera_id),
                        "cohorte_id": str(destino_cohorte_id),
                    },
                },
                filas_afectadas=clonadas,
                ip=ip,
                user_agent=user_agent,
            ),
            session=session,
        )
        return {"clonadas": clonadas, "omitidas": omitidas}

    # ── 6. Vigencia en bloque ────────────────────────────────────────

    async def modificar_vigencia_bloque(
        self,
        *,
        tenant_id: UUID,
        actor_id: UUID,
        materia_id: Optional[UUID] = None,
        carrera_id: Optional[UUID] = None,
        cohorte_id: Optional[UUID] = None,
        desde: datetime,
        hasta: Optional[datetime] = None,
        session: AsyncSession,
        ip: str = "0.0.0.0",
        user_agent: str = "service",
    ) -> Dict[str, Any]:
        """Actualiza vigencia de todas las asignaciones de un equipo.

        Todo-o-nada. Valida desde ≤ hasta.
        """
        if hasta is not None and desde > hasta:
            raise ValueError("hasta no puede ser anterior a desde")

        filas = await self._repo.bulk_update_vigencia(
            tenant_id=tenant_id,
            materia_id=materia_id,
            carrera_id=carrera_id,
            cohorte_id=cohorte_id,
            desde=desde,
            hasta=hasta,
            session=session,
        )

        await self._audit_repo.add(
            entry=AuditLog(
                tenant_id=tenant_id,
                actor_id=actor_id,
                accion="ASIGNACION_MODIFICAR",
                detalle={
                    "tipo": "vigencia_bloque",
                    "materia_id": str(materia_id) if materia_id else None,
                    "carrera_id": str(carrera_id) if carrera_id else None,
                    "cohorte_id": str(cohorte_id) if cohorte_id else None,
                    "desde": desde.isoformat(),
                    "hasta": hasta.isoformat() if hasta else None,
                },
                filas_afectadas=filas,
                ip=ip,
                user_agent=user_agent,
            ),
            session=session,
        )
        return {"filas_afectadas": filas}

    # ── 7. Export CSV ─────────────────────────────────────────────────

    async def export_equipo_csv(
        self,
        *,
        tenant_id: UUID,
        materia_id: Optional[UUID] = None,
        carrera_id: Optional[UUID] = None,
        cohorte_id: Optional[UUID] = None,
        session: AsyncSession,
    ) -> str:
        """Genera CSV con asignaciones del equipo.

        Header fijo, sin PII, comisiones con ";", fórmulas escapadas.
        """

        def _user_name(u) -> str:
            return f"{u.nombre or ''} {u.apellidos or ''}".strip()

        asignaciones = await self._repo.list_by_equipo(
            tenant_id=tenant_id,
            materia_id=materia_id,
            carrera_id=carrera_id,
            cohorte_id=cohorte_id,
            session=session,
            solo_vigentes=False,
        )

        from app.repositories.usuario_repository import UsuarioRepository

        user_repo = UsuarioRepository()
        users_map: Dict[str, Any] = {}
        for a in asignaciones:
            if str(a.usuario_id) not in users_map:
                user = await user_repo.get(id=a.usuario_id, tenant_id=tenant_id, session=session)
                if user:
                    users_map[str(a.usuario_id)] = user

        from app.models.role import Role
        from sqlalchemy import select

        role_ids = {str(a.role_id) for a in asignaciones}
        roles_map: Dict[str, str] = {}
        if role_ids:
            stmt = select(Role).where(
                Role.id.in_([UUID(rid) for rid in role_ids]),
                Role.tenant_id == tenant_id,
                Role.deleted_at.is_(None),
            )
            result = await session.execute(stmt)
            for r in result.scalars().all():
                roles_map[str(r.id)] = r.code

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "legajo", "docente", "rol",
            "materia_id", "carrera_id", "cohorte_id",
            "comisiones", "desde", "hasta", "estado",
        ])

        for a in asignaciones:
            user = users_map.get(str(a.usuario_id))
            legajo = escape_csv(user.legajo or "") if user else ""
            docente = escape_csv(_user_name(user)) if user else ""
            role_code = roles_map.get(str(a.role_id), "")
            comisiones_str = ";".join(a.comisiones or [])

            writer.writerow([
                legajo,
                docente,
                role_code,
                str(a.materia_id) if a.materia_id else "",
                str(a.carrera_id) if a.carrera_id else "",
                str(a.cohorte_id) if a.cohorte_id else "",
                comisiones_str,
                a.desde.isoformat() if a.desde else "",
                a.hasta.isoformat() if a.hasta else "",
                a.estado_vigencia,
            ])

        return output.getvalue()

"""AsignacionService — lógica de dominio para asignaciones usuario×rol×contexto (C-07).

Valida:
    - Combinación rol × contexto (tabla D3).
    - Consistencia tenant en todas las FKs.
    - Auto-supervisión prohibida (responsable_id != usuario_id).
    - Ciclos en cadena de responsables (depth ≤ 10).
    - desde ≤ hasta cuando ambas existen.
    - ADMIN y FINANZAS NO se modelan en Asignacion (van en UserRole).

Emite audit: ASIGNACION_CREAR, ASIGNACION_MODIFICAR, ASIGNACION_BAJA.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asignacion import Asignacion, ROLES_EN_ASIGNACION
from app.models.audit_log import AuditLog
from app.repositories.asignacion_repository import AsignacionRepository
from app.repositories.audit_log_repository import AuditLogRepository


# Roles NO permitidos en Asignacion (deben ir en UserRole)
_ROLES_SOLO_USER_ROLE = frozenset({"ADMIN", "FINANZAS"})

# Reglas de contexto requerido por rol (None = no aplicable / se acepta NULL)
# True = requerido, False = NO permitido (must be None), None = opcional
_ROL_CONTEXTO: Dict[str, Dict[str, Optional[bool]]] = {
    "PROFESOR": {
        "materia_id": True,
        "carrera_id": True,
        "cohorte_id": True,
    },
    "TUTOR": {
        "materia_id": True,
        "carrera_id": True,
        "cohorte_id": True,
    },
    "COORDINADOR": {
        "materia_id": None,   # opcional
        "carrera_id": True,   # requerido
        "cohorte_id": None,   # opcional
    },
    "NEXO": {
        "materia_id": None,
        "carrera_id": None,
        "cohorte_id": None,
    },
}


class AsignacionServiceError(Exception):
    """Excepción controlada del servicio de asignaciones."""

    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


class AsignacionService:
    """Servicio de gestión de asignaciones usuario×rol×contexto.

    Dependencias:
        - AsignacionRepository: acceso a datos.
        - AuditLogRepository: registro inmutable de acciones.
    """

    def __init__(
        self,
        asignacion_repo: AsignacionRepository | None = None,
        audit_repo: AuditLogRepository | None = None,
    ) -> None:
        self._repo = asignacion_repo or AsignacionRepository()
        self._audit_repo = audit_repo or AuditLogRepository()

    def _validate_rol_contexto(
        self,
        role_code: str,
        materia_id: UUID | None,
        carrera_id: UUID | None,
        cohorte_id: UUID | None,
    ) -> None:
        """Valida la combinación rol × contexto académico.

        Raises:
            AsignacionServiceError(422): si la combinación es inválida.
        """
        role_upper = role_code.upper()

        # ADMIN y FINANZAS no se modelan en Asignacion
        if role_upper in _ROLES_SOLO_USER_ROLE:
            raise AsignacionServiceError(
                status_code=422,
                detail=(
                    f"El rol {role_upper} se modela en UserRole, no en Asignacion. "
                    "Use el endpoint de RBAC para asignar roles globales de tenant."
                ),
            )

        rules = _ROL_CONTEXTO.get(role_upper)
        if rules is None:
            # Rol desconocido — rechazar por seguridad (fail-closed)
            raise AsignacionServiceError(
                status_code=422,
                detail=f"Rol desconocido para Asignacion: {role_upper}",
            )

        # Verificar campos requeridos
        ctx_map = {
            "materia_id": materia_id,
            "carrera_id": carrera_id,
            "cohorte_id": cohorte_id,
        }
        for field, required in rules.items():
            value = ctx_map[field]
            if required is True and value is None:
                raise AsignacionServiceError(
                    status_code=422,
                    detail=f"{field} es requerido para el rol {role_upper}",
                )

    async def _detect_cycle(
        self,
        *,
        nuevo_usuario_id: UUID,
        responsable_id: UUID,
        tenant_id: UUID,
        session: AsyncSession,
        max_depth: int = 10,
    ) -> bool:
        """Detecta ciclos en la cadena de responsables.

        Recorre la cadena hacia arriba desde responsable_id.
        Si en algún nivel el responsable es nuevo_usuario_id → ciclo.

        Returns:
            True si hay ciclo, False si la cadena es válida.
        """
        current_id = responsable_id
        visited: set[UUID] = {nuevo_usuario_id}

        for _ in range(max_depth):
            if current_id in visited:
                return True
            visited.add(current_id)

            # Buscar asignaciones vigentes del nodo actual para ver su responsable
            asignaciones = await self._repo.list(
                tenant_id=tenant_id,
                estado_vigencia="vigente",
                usuario_id=current_id,
                session=session,
            )
            # Tomar el primer responsable encontrado en asignaciones vigentes
            responsable_ids = [
                a.responsable_id for a in asignaciones if a.responsable_id is not None
            ]
            if not responsable_ids:
                return False  # No hay más responsables — cadena sin ciclo

            current_id = responsable_ids[0]

        # Si llegamos al límite, asumir ciclo por seguridad
        return True

    async def create(
        self,
        *,
        tenant_id: UUID,
        actor_id: UUID,
        usuario_id: UUID,
        role_id: UUID,
        role_code: str,
        desde: datetime,
        hasta: Optional[datetime] = None,
        materia_id: Optional[UUID] = None,
        carrera_id: Optional[UUID] = None,
        cohorte_id: Optional[UUID] = None,
        responsable_id: Optional[UUID] = None,
        comisiones: Optional[List[str]] = None,
        session: AsyncSession,
    ) -> Asignacion:
        """Crea una asignación con validaciones completas.

        Args:
            tenant_id: UUID del tenant (del JWT del caller).
            actor_id: UUID del actor que ejecuta.
            usuario_id: UUID del usuario asignado.
            role_id: UUID del rol.
            role_code: Código del rol (para validación de contexto).
            desde: Inicio de vigencia.
            hasta: Fin de vigencia (None = indefinida).
            materia_id: UUID de materia (nullable).
            carrera_id: UUID de carrera (nullable).
            cohorte_id: UUID de cohorte (nullable).
            responsable_id: UUID del responsable (nullable).
            comisiones: Lista de comisiones.
            session: Sesión async.

        Returns:
            Asignacion creada.

        Raises:
            AsignacionServiceError(422): si alguna validación falla.
        """
        # Validación 1: rol × contexto
        self._validate_rol_contexto(
            role_code=role_code,
            materia_id=materia_id,
            carrera_id=carrera_id,
            cohorte_id=cohorte_id,
        )

        # Validación 2: desde ≤ hasta
        if hasta is not None and desde > hasta:
            raise AsignacionServiceError(
                status_code=422,
                detail="hasta no puede ser anterior a desde",
            )

        # Validación 3: auto-supervisión prohibida
        if responsable_id is not None and responsable_id == usuario_id:
            raise AsignacionServiceError(
                status_code=422,
                detail="el responsable_id no puede ser igual al usuario_id (auto-supervisión prohibida)",
            )

        # Validación 4: ciclo en cadena de responsables
        if responsable_id is not None:
            has_cycle = await self._detect_cycle(
                nuevo_usuario_id=usuario_id,
                responsable_id=responsable_id,
                tenant_id=tenant_id,
                session=session,
            )
            if has_cycle:
                raise AsignacionServiceError(
                    status_code=422,
                    detail="ciclo detectado en la cadena de responsabilidad",
                )

        asig = await self._repo.create(
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            role_id=role_id,
            desde=desde,
            hasta=hasta,
            materia_id=materia_id,
            carrera_id=carrera_id,
            cohorte_id=cohorte_id,
            responsable_id=responsable_id,
            comisiones=comisiones or [],
            session=session,
        )

        await self._audit_repo.add(
            entry=AuditLog(
                tenant_id=tenant_id,
                actor_id=actor_id,
                accion="ASIGNACION_CREAR",
                detalle={
                    "asignacion_id": str(asig.id),
                    "usuario_id": str(usuario_id),
                    "role_id": str(role_id),
                    "role_code": role_code,
                },
                filas_afectadas=1,
                ip="0.0.0.0",
                user_agent="service",
            ),
            session=session,
        )

        return asig

    async def get(
        self,
        *,
        tenant_id: UUID,
        id: UUID,
        session: AsyncSession,
    ) -> Asignacion:
        """Retorna una asignación por ID.

        Raises:
            AsignacionServiceError(404): si no existe.
        """
        asig = await self._repo.get(id=id, tenant_id=tenant_id, session=session)
        if asig is None:
            raise AsignacionServiceError(status_code=404, detail="asignacion not found")
        return asig

    async def list(
        self,
        *,
        tenant_id: UUID,
        session: AsyncSession,
        **filters: Any,
    ) -> List[Asignacion]:
        """Lista asignaciones con filtros opcionales."""
        return await self._repo.list(tenant_id=tenant_id, session=session, **filters)

    async def delete(
        self,
        *,
        tenant_id: UUID,
        id: UUID,
        actor_id: UUID,
        session: AsyncSession,
    ) -> bool:
        """Soft-delete de una asignación.

        Returns:
            True si fue eliminada.

        Raises:
            AsignacionServiceError(404): si no existe.
        """
        asig = await self._repo.get(id=id, tenant_id=tenant_id, session=session)
        if asig is None:
            raise AsignacionServiceError(status_code=404, detail="asignacion not found")

        await self._repo.soft_delete(id=id, tenant_id=tenant_id, session=session)

        await self._audit_repo.add(
            entry=AuditLog(
                tenant_id=tenant_id,
                actor_id=actor_id,
                accion="ASIGNACION_BAJA",
                detalle={
                    "asignacion_id": str(id),
                    "usuario_id": str(asig.usuario_id),
                    "role_id": str(asig.role_id),
                },
                filas_afectadas=1,
                ip="0.0.0.0",
                user_agent="service",
            ),
            session=session,
        )

        return True

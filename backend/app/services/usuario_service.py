"""UsuarioService — lógica de dominio para la gestión de usuarios (C-07).

Orquesta UsuarioRepository + AuditLogRepository.
Emite eventos de auditoría: USUARIO_CREAR, USUARIO_MODIFICAR, USUARIO_BAJA.

Reglas:
- Email único por tenant.
- PII nunca en el detalle del audit log.
- Soft delete preserva el registro y las asignaciones históricas.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.models.user import User
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.usuario_repository import UsuarioRepository


class UsuarioServiceError(Exception):
    """Excepción controlada del servicio de usuarios."""

    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


class UsuarioService:
    """Servicio de gestión de usuarios del tenant.

    Dependencias:
        - UsuarioRepository: acceso a datos (cifrado PII incluido).
        - AuditLogRepository: registro inmutable de acciones.
    """

    def __init__(
        self,
        usuario_repo: UsuarioRepository | None = None,
        audit_repo: AuditLogRepository | None = None,
    ) -> None:
        self._usuario_repo = usuario_repo or UsuarioRepository()
        self._audit_repo = audit_repo or AuditLogRepository()

    async def create(
        self,
        *,
        tenant_id: UUID,
        actor_id: UUID,
        email: str,
        password_plain: str,
        nombre: Optional[str] = None,
        apellidos: Optional[str] = None,
        legajo: Optional[str] = None,
        legajo_profesional: Optional[str] = None,
        banco: Optional[str] = None,
        regional: Optional[str] = None,
        facturador: bool = False,
        dni: Optional[str] = None,
        cuil: Optional[str] = None,
        cbu: Optional[str] = None,
        alias_cbu: Optional[str] = None,
        session: AsyncSession,
    ) -> User:
        """Crea un usuario con cifrado de PII y emisión de audit log.

        Args:
            tenant_id: UUID del tenant (del JWT del caller).
            actor_id: UUID del usuario que ejecuta la acción.
            email: Email en claro.
            password_plain: Password en claro.
            nombre: Nombre/s.
            apellidos: Apellido/s.
            legajo: Legajo (nullable).
            legajo_profesional: Legajo profesional (nullable).
            banco: Banco (nullable).
            regional: Regional/sede (nullable).
            facturador: Flag de facturador.
            dni: DNI en claro (se cifra).
            cuil: CUIL en claro (se cifra).
            cbu: CBU en claro (se cifra).
            alias_cbu: Alias CBU en claro (se cifra).
            session: Sesión async.

        Returns:
            User creado.

        Raises:
            UsuarioServiceError(400): si el email ya existe en el tenant.
        """
        # Verificar unicidad por email en el tenant
        existing = await self._usuario_repo.get_by_email_lookup(
            email=email, tenant_id=tenant_id, session=session
        )
        if existing is not None:
            raise UsuarioServiceError(
                status_code=400,
                detail="email already exists for this tenant",
            )

        user = await self._usuario_repo.create(
            tenant_id=tenant_id,
            email=email,
            password_plain=password_plain,
            nombre=nombre,
            apellidos=apellidos,
            legajo=legajo,
            legajo_profesional=legajo_profesional,
            banco=banco,
            regional=regional,
            facturador=facturador,
            dni=dni,
            cuil=cuil,
            cbu=cbu,
            alias_cbu=alias_cbu,
            session=session,
        )

        # Audit log — SIN PII en el detalle
        await self._audit_repo.add(
            entry=AuditLog(
                tenant_id=tenant_id,
                actor_id=actor_id,
                accion="USUARIO_CREAR",
                detalle={
                    "usuario_id": str(user.id),
                    "nombre": nombre,
                    "apellidos": apellidos,
                    # Sin email, dni, cuil, cbu, alias_cbu — NUNCA PII en el detalle
                },
                filas_afectadas=1,
                ip="0.0.0.0",
                user_agent="service",
            ),
            session=session,
        )

        return user

    async def get(
        self,
        *,
        tenant_id: UUID,
        id: UUID,
        session: AsyncSession,
    ) -> User:
        """Retorna un usuario por ID y tenant.

        Raises:
            UsuarioServiceError(404): si no existe o fue soft-deleted.
        """
        user = await self._usuario_repo.get(id=id, tenant_id=tenant_id, session=session)
        if user is None:
            raise UsuarioServiceError(status_code=404, detail="usuario not found")
        return user

    async def list(
        self,
        *,
        tenant_id: UUID,
        session: AsyncSession,
        limit: int = 50,
        offset: int = 0,
    ) -> List[User]:
        """Lista usuarios activos del tenant."""
        return await self._usuario_repo.list(
            tenant_id=tenant_id, session=session, limit=limit, offset=offset
        )

    async def update(
        self,
        *,
        tenant_id: UUID,
        id: UUID,
        actor_id: UUID,
        data: Dict[str, Any],
        session: AsyncSession,
    ) -> User:
        """Actualiza un usuario con emisión de audit log.

        Raises:
            UsuarioServiceError(404): si no existe.
        """
        user = await self._usuario_repo.update(
            id=id, tenant_id=tenant_id, data=data, session=session
        )
        if user is None:
            raise UsuarioServiceError(status_code=404, detail="usuario not found")

        await self._audit_repo.add(
            entry=AuditLog(
                tenant_id=tenant_id,
                actor_id=actor_id,
                accion="USUARIO_MODIFICAR",
                detalle={
                    "usuario_id": str(id),
                    "campos_modificados": [
                        k for k in data if k not in ("dni", "cuil", "cbu", "alias_cbu", "email")
                    ],
                },
                filas_afectadas=1,
                ip="0.0.0.0",
                user_agent="service",
            ),
            session=session,
        )
        return user

    async def delete(
        self,
        *,
        tenant_id: UUID,
        id: UUID,
        actor_id: UUID,
        session: AsyncSession,
    ) -> bool:
        """Soft-delete de un usuario con emisión de audit log.

        Returns:
            True si el usuario fue eliminado.

        Raises:
            UsuarioServiceError(404): si no existe.
        """
        result = await self._usuario_repo.soft_delete(
            id=id, tenant_id=tenant_id, session=session
        )
        if not result:
            raise UsuarioServiceError(status_code=404, detail="usuario not found")

        await self._audit_repo.add(
            entry=AuditLog(
                tenant_id=tenant_id,
                actor_id=actor_id,
                accion="USUARIO_BAJA",
                detalle={"usuario_id": str(id)},
                filas_afectadas=1,
                ip="0.0.0.0",
                user_agent="service",
            ),
            session=session,
        )
        return True

    async def decrypt_pii(self, user: User) -> Dict[str, Optional[str]]:
        """Descifra y retorna la PII del usuario.

        Solo usar para callers con usuarios:gestionar.
        """
        return await self._usuario_repo.decrypt_pii(user)

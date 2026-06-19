"""UsuarioRepository — operaciones de acceso a datos para el modelo User (C-07).

Responsabilidades:
    - Cifrar PII (dni, cuil, cbu, alias_cbu, email) antes de persistir.
    - Descifrar PII al leer (vía decrypt_pii helper).
    - Filtrar SIEMPRE por tenant_id.
    - Soft delete (never hard delete).

El cifrado usa encryption_service (AES-256-GCM singleton de C-02).
El email_lookup usa email_lookup_hash (HMAC-SHA256 de C-02).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import encryption_service, email_lookup_hash, hash_password
from app.models.user import User
from app.repositories.base import BaseRepository


class UsuarioRepository(BaseRepository[User]):
    """Repositorio para el modelo User con cifrado de PII y tenant-scoping."""

    def __init__(self) -> None:
        super().__init__(User)

    async def create(
        self,
        *,
        tenant_id: UUID,
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
        """Crea un usuario cifrando PII antes de persistir.

        Args:
            tenant_id: UUID del tenant.
            email: Email en claro (se cifra + se genera lookup HMAC).
            password_plain: Password en claro (se hashea con Argon2id).
            nombre: Nombre/s (texto plano, no PII regulada).
            apellidos: Apellido/s (texto plano).
            legajo: Legajo del alumno (nullable).
            legajo_profesional: Legajo profesional (nullable).
            banco: Banco (texto plano).
            regional: Regional/sede (texto plano).
            facturador: Flag de facturador.
            dni: DNI en claro (se cifra en dni_encrypted).
            cuil: CUIL en claro (se cifra en cuil_encrypted).
            cbu: CBU en claro (se cifra en cbu_encrypted).
            alias_cbu: Alias CBU en claro (se cifra en alias_cbu_encrypted).
            session: Sesión async.

        Returns:
            User con todos sus valores generados.
        """
        user = User(
            tenant_id=tenant_id,
            email_encrypted=encryption_service.encrypt(email),
            email_lookup=email_lookup_hash(email),
            password_hash=hash_password(password_plain),
            nombre=nombre,
            apellidos=apellidos,
            legajo=legajo,
            legajo_profesional=legajo_profesional,
            banco=banco,
            regional=regional,
            facturador=facturador,
            dni_encrypted=encryption_service.encrypt(dni) if dni else None,
            cuil_encrypted=encryption_service.encrypt(cuil) if cuil else None,
            cbu_encrypted=encryption_service.encrypt(cbu) if cbu else None,
            alias_cbu_encrypted=encryption_service.encrypt(alias_cbu) if alias_cbu else None,
        )
        session.add(user)
        await session.flush()
        await session.refresh(user)
        return user

    async def get_by_email_lookup(
        self,
        *,
        email: str,
        tenant_id: UUID,
        session: AsyncSession,
    ) -> User | None:
        """Busca un usuario por email dentro de un tenant.

        Normaliza el email y calcula el HMAC para buscar en email_lookup.

        Args:
            email: Email en claro (se normaliza y hashea internamente).
            tenant_id: UUID del tenant.
            session: Sesión async.

        Returns:
            User activo si existe, None si no existe o fue soft-deleted.
        """
        lookup = email_lookup_hash(email)
        stmt = select(self.model).where(
            self.model.email_lookup == lookup,
            self.model.tenant_id == tenant_id,
            self.model.deleted_at.is_(None),
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def update(
        self,
        *,
        id: UUID,
        tenant_id: UUID,
        data: Dict[str, Any],
        session: AsyncSession,
    ) -> Optional[User]:
        """Actualiza campos de un usuario, cifrando PII si viene.

        Args:
            id: UUID del usuario.
            tenant_id: UUID del tenant.
            data: Dict con campos a actualizar (en claro para PII).
            session: Sesión async.

        Returns:
            User actualizado o None si no existe.
        """
        user = await self.get(id=id, tenant_id=tenant_id, session=session)
        if user is None:
            return None

        # Campos PII — cifrar si vienen
        if "email" in data and data["email"] is not None:
            user.email_encrypted = encryption_service.encrypt(data.pop("email"))
            user.email_lookup = email_lookup_hash(data.pop("email", user.email_encrypted))
        if "dni" in data:
            user.dni_encrypted = (
                encryption_service.encrypt(data.pop("dni")) if data["dni"] else None
            )
            data.pop("dni", None)
        if "cuil" in data:
            user.cuil_encrypted = (
                encryption_service.encrypt(data.pop("cuil")) if data["cuil"] else None
            )
            data.pop("cuil", None)
        if "cbu" in data:
            user.cbu_encrypted = (
                encryption_service.encrypt(data.pop("cbu")) if data["cbu"] else None
            )
            data.pop("cbu", None)
        if "alias_cbu" in data:
            user.alias_cbu_encrypted = (
                encryption_service.encrypt(data.pop("alias_cbu")) if data["alias_cbu"] else None
            )
            data.pop("alias_cbu", None)

        # Campos no PII — actualizar directamente
        for field, value in data.items():
            if hasattr(user, field):
                setattr(user, field, value)

        await session.flush()
        await session.refresh(user)
        return user

    async def decrypt_pii(self, user: User) -> Dict[str, Optional[str]]:
        """Descifra y retorna los campos PII de un usuario.

        Args:
            user: Instancia de User con campos _encrypted.

        Returns:
            Dict con {dni, cuil, cbu, alias_cbu} en claro (None si el campo era None).
        """
        return {
            "dni": encryption_service.decrypt(user.dni_encrypted) if user.dni_encrypted else None,
            "cuil": encryption_service.decrypt(user.cuil_encrypted) if user.cuil_encrypted else None,
            "cbu": encryption_service.decrypt(user.cbu_encrypted) if user.cbu_encrypted else None,
            "alias_cbu": (
                encryption_service.decrypt(user.alias_cbu_encrypted)
                if user.alias_cbu_encrypted else None
            ),
        }

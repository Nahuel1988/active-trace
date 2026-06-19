"""PerfilService — lógica de negocio para el perfil propio del usuario (C-20).

Reglas:
    - La identidad del usuario SIEMPRE viene del JWT (user_id param), nunca del body.
    - CUIL es solo lectura: update_perfil excluye cuil de data antes de persistir.
    - PII (dni, cbu, alias_cbu) se cifra en el repository (UsuarioRepository.update).
    - get_perfil descifra PII para el dueño y la incluye en la respuesta.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.usuario_repository import UsuarioRepository


class PerfilService:
    """Servicio para leer y actualizar el perfil propio del usuario de la sesión."""

    def __init__(self, usuario_repo: UsuarioRepository) -> None:
        self._repo = usuario_repo

    async def get_perfil(
        self,
        *,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        session: AsyncSession,
    ) -> Dict[str, Any]:
        """Lee el perfil del usuario y descifra la PII para el dueño.

        Args:
            tenant_id: Tenant de la sesión.
            user_id: UUID del usuario (siempre del JWT).
            session: Sesión async.

        Returns:
            Dict con todos los campos del perfil, PII descifrada.

        Raises:
            ValueError: Si el usuario no existe en el tenant.
        """
        user = await self._repo.get_perfil(
            tenant_id=tenant_id, user_id=user_id, session=session
        )
        if user is None:
            msg = f"Usuario {user_id} no encontrado en tenant {tenant_id}"
            raise ValueError(msg)

        pii = await self._repo.decrypt_pii(user)

        return {
            "id": str(user.id),
            "tenant_id": str(user.tenant_id),
            "nombre": user.nombre,
            "apellidos": user.apellidos,
            "legajo": user.legajo,
            "legajo_profesional": user.legajo_profesional,
            "banco": user.banco,
            "regional": user.regional,
            "facturador": user.facturador or False,
            "is_active": user.is_active,
            "modalidad_cobro": user.modalidad_cobro,
            # PII descifrada — solo para el dueño
            "dni": pii.get("dni"),
            "cuil": pii.get("cuil"),
            "cbu": pii.get("cbu"),
            "alias_cbu": pii.get("alias_cbu"),
        }

    async def update_perfil(
        self,
        *,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        data: Dict[str, Any],
        session: AsyncSession,
    ) -> User:
        """Actualiza el perfil del usuario de la sesión.

        CUIL es excluido automáticamente (solo lectura).
        PII (dni, cbu, alias_cbu) se cifra en el repository.

        Args:
            tenant_id: Tenant de la sesión.
            user_id: UUID del usuario (siempre del JWT).
            data: Campos a actualizar (en claro para PII).
            session: Sesión async.

        Returns:
            User actualizado.

        Raises:
            ValueError: Si el usuario no existe en el tenant.
        """
        user = await self._repo.update_perfil(
            tenant_id=tenant_id, user_id=user_id, data=data, session=session
        )
        if user is None:
            msg = f"Usuario {user_id} no encontrado en tenant {tenant_id}"
            raise ValueError(msg)
        return user

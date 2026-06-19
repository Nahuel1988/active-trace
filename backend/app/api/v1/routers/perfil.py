"""Router de perfil propio — C-20.

Endpoints:
    GET  /api/v1/perfil   — lee el perfil del usuario de la sesión
    PATCH /api/v1/perfil  — actualiza campos editables del perfil

Identidad SIEMPRE del JWT (get_current_user), nunca de URL / body.
CUIL es solo lectura: el schema PerfilUpdate no lo declara (extra='forbid' → 422).
No reimplementa logout — reutiliza POST /api/auth/logout de C-03.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.repositories.usuario_repository import UsuarioRepository
from app.schemas.perfil import PerfilRead, PerfilUpdate
from app.services.perfil_service import PerfilService

router = APIRouter(
    prefix="/api/v1/perfil",
    tags=["perfil"],
)


def _get_service() -> PerfilService:
    return PerfilService(usuario_repo=UsuarioRepository())


@router.get("", response_model=PerfilRead)
async def get_perfil(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: PerfilService = Depends(_get_service),
) -> PerfilRead:
    """Lee el perfil del usuario autenticado con PII descifrada.

    La identidad se extrae EXCLUSIVAMENTE del JWT verificado.
    Nunca de parámetros de URL, body o query.
    """
    try:
        perfil_data = await service.get_perfil(
            tenant_id=current_user.tenant_id,
            user_id=current_user.id,
            session=db,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return PerfilRead(**perfil_data)


@router.patch("", response_model=PerfilRead)
async def update_perfil(
    body: PerfilUpdate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: PerfilService = Depends(_get_service),
) -> PerfilRead:
    """Actualiza los campos editables del perfil del usuario de la sesión.

    - Identidad del usuario SIEMPRE del JWT (no del body).
    - CUIL no está en PerfilUpdate → extra='forbid' devuelve 422 si se envía.
    - PII (dni, cbu, alias_cbu) se cifra automáticamente.
    """
    # Solo actualizar campos provistos (exclude_none=True para actualización parcial)
    data = body.model_dump(exclude_none=True)

    try:
        await service.update_perfil(
            tenant_id=current_user.tenant_id,
            user_id=current_user.id,
            data=data,
            session=db,
        )
        # Re-leer el perfil para devolver el estado actualizado con PII descifrada
        perfil_data = await service.get_perfil(
            tenant_id=current_user.tenant_id,
            user_id=current_user.id,
            session=db,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return PerfilRead(**perfil_data)

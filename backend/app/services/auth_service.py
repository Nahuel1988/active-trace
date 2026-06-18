"""AuthService — autenticación y orquestación de login.

Flujo::

                     authenticate()
                          │
                    ┌─────┴─────┐
                    │ 2FA on?   │
                    └─────┬─────┘
                     yes  │  no
                   ┌──────┘
                   ▼
           create_challenge     issue_token_pair
           (TotpService)        (TokenService)

Uso::

    from app.services.auth_service import AuthService
    service = AuthService(user_repo=UserRepository())
    user = await service.authenticate(email, password, tenant_id, session)
    result = await service.login(email, password, tenant_id, totp_service,
                                 token_service, session)
"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import email_lookup_hash, verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.services.token_service import AuthError, TokenService
from app.services.totp_service import TotpService

_UNIFORM_AUTH_ERROR = "Credenciales inválidas"


class AuthService:
    """Servicio de autenticación y orquestación de login.

    Attributes:
        _user_repo: Repositorio de usuarios.
    """

    def __init__(self, user_repo: UserRepository) -> None:
        self._user_repo = user_repo

    async def authenticate(
        self,
        email: str,
        password: str,
        tenant_id: UUID,
        session: AsyncSession,
    ) -> User:
        """Validate credentials.

        Args:
            email: Email del usuario (se normaliza internamente).
            password: Password en texto plano.
            tenant_id: UUID del tenant.
            session: Sesión de base de datos async.

        Returns:
            User si las credenciales son válidas.

        Raises:
            AuthError: 401 con mensaje uniforme si las credenciales
                son inválidas, el email no existe o el usuario está
                inactivo.
        """
        lookup = email_lookup_hash(email)
        user = await self._user_repo.get_active_by_email_lookup(
            tenant_id=tenant_id,
            email_lookup=lookup,
            session=session,
        )

        if user is None:
            raise AuthError(status_code=401, detail=_UNIFORM_AUTH_ERROR)

        if not verify_password(password, user.password_hash):
            raise AuthError(status_code=401, detail=_UNIFORM_AUTH_ERROR)

        if not user.is_active:
            raise AuthError(status_code=401, detail=_UNIFORM_AUTH_ERROR)

        return user

    async def login(
        self,
        email: str,
        password: str,
        tenant_id: UUID,
        totp_service: TotpService,
        token_service: TokenService,
        session: AsyncSession,
    ) -> dict:
        """Authenticate and either issue token pair or return 2FA challenge.

        Args:
            email: Email del usuario.
            password: Password en texto plano.
            tenant_id: UUID del tenant.
            totp_service: Instancia de TotpService.
            token_service: Instancia de TokenService.
            session: Sesión de base de datos async.

        Returns:
            ``TokenPair`` dict si 2FA está deshabilitado, ó
            ``TwoFAChallenge`` dict si 2FA está habilitado.

        Raises:
            AuthError: 401 si las credenciales son inválidas.
        """
        user = await self.authenticate(email, password, tenant_id, session)

        if user.totp_enabled:
            challenge = totp_service.create_challenge(user)
            return {"challenge": challenge, "type": "2fa_challenge"}

        return await token_service.issue_token_pair(user, session)

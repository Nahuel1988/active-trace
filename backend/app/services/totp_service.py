"""TotpService — TOTP/2FA enrollment, confirmation, verification and challenge.

Orchestrates the full 2FA lifecycle:
- **enroll**: generate + persist encrypted TOTP secret
- **confirm**: verify a code to enable 2FA
- **create_challenge**: short-lived JWT for the 2FA gate
- **verify_and_issue**: validate challenge + code → token pair

All TOTP verifications use ``valid_window=1`` for clock drift tolerance
(accepts codes from ±1 time step / ~30 s).
"""

from datetime import datetime, timedelta, timezone

import jwt
import pyotp

from app.core.config import Settings
from app.core.security import EncryptionService
from app.models.user import User
from app.repositories.totp_secret_repository import TotpSecretRepository
from sqlalchemy.ext.asyncio import AsyncSession


class TotpService:
    """Service for TOTP/2FA operations."""

    def __init__(
        self,
        totp_repo: TotpSecretRepository,
        encryption_service: EncryptionService,
    ) -> None:
        self._repo = totp_repo
        self._encryption = encryption_service

    async def enroll(self, user: User, session: AsyncSession) -> dict:
        """Generate and persist a TOTP secret for *user*.

        Does **not** set ``user.totp_enabled`` — that happens at confirm.

        Returns
            ``{"secret": <plaintext>, "otpauth_uri": <provisioning URI>}``.
        """
        secret = pyotp.random_base32()
        encrypted = self._encryption.encrypt(secret)
        await self._repo.upsert(
            user_id=user.id,
            tenant_id=user.tenant_id,
            secret_encrypted=encrypted,
            session=session,
        )
        totp = pyotp.TOTP(secret)
        uri = totp.provisioning_uri(
            name=user.email_encrypted,
            issuer_name="activia-trace",
        )
        return {"secret": secret, "otpauth_uri": uri}

    async def confirm(self, user: User, code: str, session: AsyncSession) -> bool:
        """Confirm 2FA enrollment by verifying a TOTP code.

        Uses ``valid_window=1`` for clock drift tolerance.

        * Valid code → sets ``confirmed_at`` and ``user.totp_enabled = True``.
        * Invalid code → returns ``False``, ``totp_enabled`` stays ``False``.

        Returns
            ``True`` if the code was accepted and 2FA is now enabled.
        """
        totp_secret = await self._repo.get_by_user(
            user_id=user.id,
            tenant_id=user.tenant_id,
            session=session,
        )
        if totp_secret is None:
            return False

        secret = self._encryption.decrypt(totp_secret.secret_encrypted)
        if pyotp.TOTP(secret).verify(code, valid_window=1):
            await self._repo.confirm(
                user_id=user.id,
                tenant_id=user.tenant_id,
                session=session,
            )
            user.totp_enabled = True
            return True
        return False

    def create_challenge(self, user: User) -> str:
        """Create a short-lived 2FA challenge JWT.

        The challenge expires after ``twofa_challenge_expire_minutes``
        (from ``Settings``).

        Returns
            Signed JWT with type ``2fa_challenge``.
        """
        settings = Settings()
        now = datetime.now(timezone.utc)
        payload = {
            "sub": str(user.id),
            "tenant_id": str(user.tenant_id),
            "type": "2fa_challenge",
            "iat": int(now.timestamp()),
            "exp": int(
                (
                    now
                    + timedelta(minutes=settings.twofa_challenge_expire_minutes)
                ).timestamp()
            ),
        }
        return jwt.encode(payload, settings.secret_key, algorithm="HS256")

    async def verify_and_issue(
        self,
        user: User,
        challenge_token: str,
        code: str,
        token_service,
        session: AsyncSession,
    ) -> dict:
        """Verify a 2FA challenge and issue a token pair if valid.

        Args:
            user: The user to authenticate.
            challenge_token: The 2FA challenge JWT.
            code: The TOTP code.
            token_service: Service with ``issue_token_pair(user) -> dict``.
            session: Database session.

        Returns
            Token pair dict from ``token_service.issue_token_pair()``.

        Raises
            ValueError: If the challenge is invalid, expired, or the code
                is wrong.
        """
        settings = Settings()
        try:
            payload = jwt.decode(
                challenge_token,
                settings.secret_key,
                algorithms=["HS256"],
            )
        except jwt.ExpiredSignatureError as exc:
            raise ValueError("2FA challenge has expired") from exc
        except jwt.PyJWTError as exc:
            raise ValueError("Invalid 2FA challenge") from exc

        if payload.get("type") != "2fa_challenge":
            raise ValueError("Invalid challenge type")
        if payload.get("sub") != str(user.id):
            raise ValueError("Challenge user mismatch")

        totp_secret = await self._repo.get_by_user(
            user_id=user.id,
            tenant_id=user.tenant_id,
            session=session,
        )
        if totp_secret is None:
            raise ValueError("2FA is not configured for this user")

        secret = self._encryption.decrypt(totp_secret.secret_encrypted)
        if not pyotp.TOTP(secret).verify(code, valid_window=1):
            raise ValueError("Invalid TOTP code")

        return await token_service.issue_token_pair(user=user, session=session)

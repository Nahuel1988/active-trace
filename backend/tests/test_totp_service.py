"""Tests for TotpService — strict TDD (RED → GREEN → TRIANGULATE).

Covers:
- 7.1  enroll: persists encrypted secret, totp_enabled stays False
- 7.2  confirm: valid code activates 2FA, invalid code returns False
- 7.3  create_challenge + verify_and_issue: token pair or ValueError
- 7.4  Drift tolerance: ±1 time step (30 s) codes are accepted
"""

import uuid
from datetime import datetime, timedelta, timezone

import jwt
import pyotp
import pytest
from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.config import Settings
from app.core.database import Base
from app.core.security import (
    email_lookup_hash,
    encryption_service,
    hash_password,
)
from app.models.totp_secret import TotpSecret
from app.models.user import User

pytestmark = pytest.mark.requires_db


# ===========================================================================
# Helpers
# ===========================================================================


async def _ensure_tables(settings: Settings) -> None:
    """Create the minimal table set for a test.
    Idempotent — safe to call multiple times.
    """
    from app.models.tenant import Tenant

    url = settings.test_database_url or settings.database_url
    async with create_async_engine(url, poolclass=NullPool).begin() as conn:
        await conn.run_sync(
            Base.metadata.create_all,
            tables=[Tenant.__table__, User.__table__, TotpSecret.__table__],
        )


class MockTokenService:
    """Dummy token service that returns a deterministic token pair."""

    async def issue_token_pair(
        self,
        user: User,
        session: AsyncSession | None = None,
    ) -> dict:
        return {
            "access_token": f"mock-access-{user.id}",
            "refresh_token": f"mock-refresh-{user.id}",
            "token_type": "bearer",
        }


# ===========================================================================
# 7.1 RED → GREEN: enroll
# ===========================================================================


@pytest.mark.requires_db
class TestEnroll:
    """Scenario: user enrolls in 2FA."""

    async def test_enroll_persists_encrypted_secret_and_totp_not_enabled(
        self,
        db_session: AsyncSession,
        settings: Settings,
    ) -> None:
        """WHEN user enrolls, THEN secret persisted encrypted, totp_enabled stays False."""
        await _ensure_tables(settings)

        from app.models.tenant import Tenant
        from app.repositories.totp_secret_repository import TotpSecretRepository
        from app.services.totp_service import TotpService

        # Arrange
        tenant = Tenant(
            id=uuid.uuid4(),
            slug=f"enroll-{uuid.uuid4().hex[:8]}",
            nombre="Enroll Test",
        )
        db_session.add(tenant)
        await db_session.flush()

        user = User(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            email_encrypted=encryption_service.encrypt("enroll@example.com"),
            email_lookup=email_lookup_hash("enroll@example.com"),
            password_hash=hash_password("password123"),
            is_active=True,
            totp_enabled=False,
        )
        db_session.add(user)
        await db_session.flush()

        svc = TotpService(
            totp_repo=TotpSecretRepository(),
            encryption_service=encryption_service,
        )

        # Act
        result = await svc.enroll(user, db_session)

        # Assert — result shape
        assert "secret" in result
        assert isinstance(result["secret"], str)
        assert len(result["secret"]) > 0
        assert "otpauth_uri" in result
        assert result["otpauth_uri"].startswith("otpauth://")

        # Assert — totp_enabled stays False
        assert user.totp_enabled is False

        # Assert — encrypted secret persisted
        repo = TotpSecretRepository()
        stored = await repo.get_by_user(
            user_id=user.id,
            tenant_id=user.tenant_id,
            session=db_session,
        )
        assert stored is not None
        assert stored.secret_encrypted != result["secret"]  # encrypted ≠ plain
        assert stored.confirmed_at is None

    async def test_enroll_returns_valid_otpauth_uri(
        self,
        db_session: AsyncSession,
        settings: Settings,
    ) -> None:
        """WHEN user enrolls, THEN returned otpauth_uri matches generated secret."""
        await _ensure_tables(settings)

        from app.models.tenant import Tenant
        from app.repositories.totp_secret_repository import TotpSecretRepository
        from app.services.totp_service import TotpService

        # Arrange
        tenant = Tenant(
            id=uuid.uuid4(),
            slug=f"uri-{uuid.uuid4().hex[:8]}",
            nombre="URI Test",
        )
        db_session.add(tenant)
        await db_session.flush()

        user = User(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            email_encrypted=encryption_service.encrypt("uri@example.com"),
            email_lookup=email_lookup_hash("uri@example.com"),
            password_hash=hash_password("password123"),
            is_active=True,
            totp_enabled=False,
        )
        db_session.add(user)
        await db_session.flush()

        svc = TotpService(
            totp_repo=TotpSecretRepository(),
            encryption_service=encryption_service,
        )

        # Act
        result = await svc.enroll(user, db_session)

        # Assert — URI is valid for the returned secret
        expected_uri = pyotp.TOTP(result["secret"]).provisioning_uri(
            name=user.email_encrypted,
            issuer_name="activia-trace",
        )
        assert result["otpauth_uri"] == expected_uri
        assert "activia-trace" in result["otpauth_uri"]


# ===========================================================================
# 7.2 RED → GREEN → TRIANGULATE: confirm
# ===========================================================================


@pytest.mark.requires_db
class TestConfirm:
    """Scenario: user confirms 2FA with a TOTP code."""

    async def test_confirm_valid_code_sets_totp_enabled(
        self,
        db_session: AsyncSession,
        settings: Settings,
    ) -> None:
        """GIVEN enrolled user, WHEN valid code, THEN totp_enabled=True and confirmed_at set."""
        await _ensure_tables(settings)

        from app.models.tenant import Tenant
        from app.repositories.totp_secret_repository import TotpSecretRepository
        from app.services.totp_service import TotpService

        # Arrange
        tenant = Tenant(
            id=uuid.uuid4(),
            slug=f"conf-{uuid.uuid4().hex[:8]}",
            nombre="Confirm Test",
        )
        db_session.add(tenant)
        await db_session.flush()

        user = User(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            email_encrypted=encryption_service.encrypt("confirm@example.com"),
            email_lookup=email_lookup_hash("confirm@example.com"),
            password_hash=hash_password("password123"),
            is_active=True,
            totp_enabled=False,
        )
        db_session.add(user)
        await db_session.flush()

        svc = TotpService(
            totp_repo=TotpSecretRepository(),
            encryption_service=encryption_service,
        )
        result = await svc.enroll(user, db_session)
        secret = result["secret"]
        valid_code = pyotp.TOTP(secret).now()

        # Act
        confirmed = await svc.confirm(user, valid_code, db_session)

        # Assert
        assert confirmed is True
        assert user.totp_enabled is True

        repo = TotpSecretRepository()
        stored = await repo.get_by_user(
            user_id=user.id,
            tenant_id=user.tenant_id,
            session=db_session,
        )
        assert stored is not None
        assert stored.confirmed_at is not None

    async def test_confirm_invalid_code_returns_false(
        self,
        db_session: AsyncSession,
        settings: Settings,
    ) -> None:
        """GIVEN enrolled user, WHEN invalid code, THEN returns False, totp_enabled stays False."""
        await _ensure_tables(settings)

        from app.models.tenant import Tenant
        from app.repositories.totp_secret_repository import TotpSecretRepository
        from app.services.totp_service import TotpService

        # Arrange
        tenant = Tenant(
            id=uuid.uuid4(),
            slug=f"bad-{uuid.uuid4().hex[:8]}",
            nombre="Bad Code Test",
        )
        db_session.add(tenant)
        await db_session.flush()

        user = User(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            email_encrypted=encryption_service.encrypt("badcode@example.com"),
            email_lookup=email_lookup_hash("badcode@example.com"),
            password_hash=hash_password("password123"),
            is_active=True,
            totp_enabled=False,
        )
        db_session.add(user)
        await db_session.flush()

        svc = TotpService(
            totp_repo=TotpSecretRepository(),
            encryption_service=encryption_service,
        )
        await svc.enroll(user, db_session)

        # Act
        confirmed = await svc.confirm(user, "000000", db_session)

        # Assert
        assert confirmed is False
        assert user.totp_enabled is False

    async def test_confirm_no_enrollment_returns_false(
        self,
        db_session: AsyncSession,
        settings: Settings,
    ) -> None:
        """GIVEN user without enrollment, WHEN confirm, THEN returns False."""
        await _ensure_tables(settings)

        from app.models.tenant import Tenant
        from app.repositories.totp_secret_repository import TotpSecretRepository
        from app.services.totp_service import TotpService

        # Arrange
        tenant = Tenant(
            id=uuid.uuid4(),
            slug=f"noenroll-{uuid.uuid4().hex[:8]}",
            nombre="No Enroll Test",
        )
        db_session.add(tenant)
        await db_session.flush()

        user = User(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            email_encrypted=encryption_service.encrypt("noenroll@example.com"),
            email_lookup=email_lookup_hash("noenroll@example.com"),
            password_hash=hash_password("password123"),
            is_active=True,
            totp_enabled=False,
        )
        db_session.add(user)
        await db_session.flush()

        svc = TotpService(
            totp_repo=TotpSecretRepository(),
            encryption_service=encryption_service,
        )

        # Act — no enrollment before confirm
        confirmed = await svc.confirm(user, "123456", db_session)

        # Assert
        assert confirmed is False


# ===========================================================================
# 7.3 RED → GREEN → TRIANGULATE: challenge + verify
# ===========================================================================


@pytest.mark.requires_db
class TestChallengeAndVerify:
    """Scenario: 2FA challenge creation and verification."""

    async def test_create_challenge_returns_valid_jwt(
        self,
        db_session: AsyncSession,
        settings: Settings,
    ) -> None:
        """WHEN creating challenge for user, THEN returns valid JWT with type 2fa_challenge."""
        from app.models.tenant import Tenant
        from app.repositories.totp_secret_repository import TotpSecretRepository
        from app.services.totp_service import TotpService

        await _ensure_tables(settings)

        # Arrange
        tenant = Tenant(
            id=uuid.uuid4(),
            slug=f"chal-{uuid.uuid4().hex[:8]}",
            nombre="Challenge Test",
        )
        db_session.add(tenant)
        user = User(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            email_encrypted=encryption_service.encrypt("chal@example.com"),
            email_lookup=email_lookup_hash("chal@example.com"),
            password_hash=hash_password("x"),
            is_active=True,
            totp_enabled=False,
        )
        db_session.add_all([tenant, user])
        await db_session.flush()

        svc = TotpService(
            totp_repo=TotpSecretRepository(),
            encryption_service=encryption_service,
        )

        # Act
        challenge = svc.create_challenge(user)

        # Assert
        payload = jwt.decode(challenge, settings.secret_key, algorithms=["HS256"])
        assert payload["type"] == "2fa_challenge"
        assert payload["sub"] == str(user.id)
        assert payload["tenant_id"] == str(user.tenant_id)
        assert "exp" in payload
        assert "iat" in payload

    async def test_verify_valid_code_returns_token_pair(
        self,
        db_session: AsyncSession,
        settings: Settings,
    ) -> None:
        """GIVEN enrolled+confirmed user, WHEN valid code+challenge, THEN token pair."""
        await _ensure_tables(settings)

        from app.models.tenant import Tenant
        from app.repositories.totp_secret_repository import TotpSecretRepository
        from app.services.totp_service import TotpService

        # Arrange
        tenant = Tenant(
            id=uuid.uuid4(),
            slug=f"verify-{uuid.uuid4().hex[:8]}",
            nombre="Verify Test",
        )
        db_session.add(tenant)
        await db_session.flush()

        user = User(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            email_encrypted=encryption_service.encrypt("verify@example.com"),
            email_lookup=email_lookup_hash("verify@example.com"),
            password_hash=hash_password("x"),
            is_active=True,
            totp_enabled=False,
        )
        db_session.add(user)
        await db_session.flush()

        svc = TotpService(
            totp_repo=TotpSecretRepository(),
            encryption_service=encryption_service,
        )

        # Enroll + confirm
        result = await svc.enroll(user, db_session)
        secret = result["secret"]
        valid_code = pyotp.TOTP(secret).now()
        await svc.confirm(user, valid_code, db_session)

        # Create challenge
        challenge = svc.create_challenge(user)

        token_service = MockTokenService()

        # Act
        token_pair = await svc.verify_and_issue(
            user, challenge, valid_code, token_service, db_session,
        )

        # Assert
        assert token_pair["access_token"] == f"mock-access-{user.id}"
        assert token_pair["refresh_token"] == f"mock-refresh-{user.id}"
        assert token_pair["token_type"] == "bearer"

    async def test_verify_invalid_code_raises_value_error(
        self,
        db_session: AsyncSession,
        settings: Settings,
    ) -> None:
        """GIVEN enrolled user, WHEN invalid code, THEN ValueError."""
        await _ensure_tables(settings)

        from app.models.tenant import Tenant
        from app.repositories.totp_secret_repository import TotpSecretRepository
        from app.services.totp_service import TotpService

        # Arrange
        tenant = Tenant(
            id=uuid.uuid4(),
            slug=f"badcode-{uuid.uuid4().hex[:8]}",
            nombre="Bad Verify",
        )
        db_session.add(tenant)
        await db_session.flush()

        user = User(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            email_encrypted=encryption_service.encrypt("badverify@example.com"),
            email_lookup=email_lookup_hash("badverify@example.com"),
            password_hash=hash_password("x"),
            is_active=True,
            totp_enabled=False,
        )
        db_session.add(user)
        await db_session.flush()

        svc = TotpService(
            totp_repo=TotpSecretRepository(),
            encryption_service=encryption_service,
        )

        result = await svc.enroll(user, db_session)
        secret = result["secret"]
        valid_code = pyotp.TOTP(secret).now()
        await svc.confirm(user, valid_code, db_session)

        challenge = svc.create_challenge(user)
        token_service = MockTokenService()

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid TOTP code"):
            await svc.verify_and_issue(
                user, challenge, "000000", token_service, db_session,
            )

    async def test_verify_expired_challenge_raises_value_error(
        self,
        db_session: AsyncSession,
        settings: Settings,
    ) -> None:
        """GIVEN expired challenge, WHEN verify, THEN ValueError."""
        await _ensure_tables(settings)

        from app.models.tenant import Tenant
        from app.repositories.totp_secret_repository import TotpSecretRepository
        from app.services.totp_service import TotpService

        # Arrange
        tenant = Tenant(
            id=uuid.uuid4(),
            slug=f"expired-{uuid.uuid4().hex[:8]}",
            nombre="Expired Test",
        )
        db_session.add(tenant)
        await db_session.flush()

        user = User(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            email_encrypted=encryption_service.encrypt("expired@example.com"),
            email_lookup=email_lookup_hash("expired@example.com"),
            password_hash=hash_password("x"),
            is_active=True,
            totp_enabled=False,
        )
        db_session.add(user)
        await db_session.flush()

        svc = TotpService(
            totp_repo=TotpSecretRepository(),
            encryption_service=encryption_service,
        )
        result = await svc.enroll(user, db_session)
        secret = result["secret"]
        valid_code = pyotp.TOTP(secret).now()
        await svc.confirm(user, valid_code, db_session)
        token_service = MockTokenService()

        # Create an already-expired challenge
        now = datetime.now(timezone.utc)
        expired_payload = {
            "sub": str(user.id),
            "tenant_id": str(user.tenant_id),
            "type": "2fa_challenge",
            "iat": int((now - timedelta(hours=1)).timestamp()),
            "exp": int((now - timedelta(minutes=1)).timestamp()),
        }
        expired_challenge = jwt.encode(
            expired_payload, settings.secret_key, algorithm="HS256",
        )

        # Act & Assert
        with pytest.raises(ValueError, match="2FA challenge has expired"):
            await svc.verify_and_issue(
                user, expired_challenge, valid_code, token_service, db_session,
            )

    async def test_verify_bad_challenge_signature_raises_value_error(
        self,
        db_session: AsyncSession,
        settings: Settings,
    ) -> None:
        """GIVEN challenge with wrong key, WHEN verify, THEN ValueError."""
        await _ensure_tables(settings)

        from app.models.tenant import Tenant
        from app.repositories.totp_secret_repository import TotpSecretRepository
        from app.services.totp_service import TotpService

        # Arrange
        tenant = Tenant(
            id=uuid.uuid4(),
            slug=f"badsig-{uuid.uuid4().hex[:8]}",
            nombre="Bad Sig Test",
        )
        db_session.add(tenant)
        await db_session.flush()

        user = User(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            email_encrypted=encryption_service.encrypt("badsig@example.com"),
            email_lookup=email_lookup_hash("badsig@example.com"),
            password_hash=hash_password("x"),
            is_active=True,
            totp_enabled=False,
        )
        db_session.add(user)
        await db_session.flush()

        svc = TotpService(
            totp_repo=TotpSecretRepository(),
            encryption_service=encryption_service,
        )
        result = await svc.enroll(user, db_session)
        secret = result["secret"]
        valid_code = pyotp.TOTP(secret).now()
        await svc.confirm(user, valid_code, db_session)
        token_service = MockTokenService()

        # Create challenge signed with a DIFFERENT key
        wrong_key = "x" * 32  # not the real secret_key
        payload = {
            "sub": str(user.id),
            "tenant_id": str(user.tenant_id),
            "type": "2fa_challenge",
            "iat": int(datetime.now(timezone.utc).timestamp()),
            "exp": int((datetime.now(timezone.utc) + timedelta(minutes=5)).timestamp()),
        }
        bad_challenge = jwt.encode(payload, wrong_key, algorithm="HS256")

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid 2FA challenge"):
            await svc.verify_and_issue(
                user, bad_challenge, valid_code, token_service, db_session,
            )

    async def test_verify_wrong_user_raises_value_error(
        self,
        db_session: AsyncSession,
        settings: Settings,
    ) -> None:
        """GIVEN challenge for user A, WHEN user B tries to use it, THEN ValueError."""
        await _ensure_tables(settings)

        from app.models.tenant import Tenant
        from app.repositories.totp_secret_repository import TotpSecretRepository
        from app.services.totp_service import TotpService

        # Arrange
        tenant = Tenant(
            id=uuid.uuid4(),
            slug=f"wronguser-{uuid.uuid4().hex[:8]}",
            nombre="Wrong User Test",
        )
        db_session.add(tenant)
        await db_session.flush()

        # User A — enrolled
        user_a = User(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            email_encrypted=encryption_service.encrypt("usera@example.com"),
            email_lookup=email_lookup_hash("usera@example.com"),
            password_hash=hash_password("x"),
            is_active=True,
            totp_enabled=False,
        )
        db_session.add(user_a)
        await db_session.flush()

        svc = TotpService(
            totp_repo=TotpSecretRepository(),
            encryption_service=encryption_service,
        )
        result = await svc.enroll(user_a, db_session)
        secret = result["secret"]
        valid_code = pyotp.TOTP(secret).now()
        await svc.confirm(user_a, valid_code, db_session)

        # Challenge for user A
        challenge = svc.create_challenge(user_a)
        token_service = MockTokenService()

        # User B — different user
        user_b = User(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            email_encrypted=encryption_service.encrypt("userb@example.com"),
            email_lookup=email_lookup_hash("userb@example.com"),
            password_hash=hash_password("x"),
            is_active=True,
            totp_enabled=False,
        )
        db_session.add(user_b)
        await db_session.flush()

        # Act & Assert — user_b tries to use user_a's challenge
        with pytest.raises(ValueError, match="Challenge user mismatch"):
            await svc.verify_and_issue(
                user_b, challenge, valid_code, token_service, db_session,
            )


# ===========================================================================
# 7.4 TRIANGULATE: Drift tolerance ±1 step
# ===========================================================================


@pytest.mark.requires_db
class TestDriftTolerance:
    """Scenario: codes from adjacent time steps (±30 s) are accepted."""

    async def test_verify_with_previous_time_step(
        self,
        db_session: AsyncSession,
        settings: Settings,
    ) -> None:
        """GIVEN enrolled user, WHEN code from 30 s ago, THEN accepted (valid_window=1)."""
        await _ensure_tables(settings)

        from app.models.tenant import Tenant
        from app.repositories.totp_secret_repository import TotpSecretRepository
        from app.services.totp_service import TotpService

        # Arrange
        tenant = Tenant(
            id=uuid.uuid4(),
            slug=f"prevstep-{uuid.uuid4().hex[:8]}",
            nombre="Prev Step Test",
        )
        db_session.add(tenant)
        await db_session.flush()

        user = User(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            email_encrypted=encryption_service.encrypt("prevstep@example.com"),
            email_lookup=email_lookup_hash("prevstep@example.com"),
            password_hash=hash_password("x"),
            is_active=True,
            totp_enabled=False,
        )
        db_session.add(user)
        await db_session.flush()

        svc = TotpService(
            totp_repo=TotpSecretRepository(),
            encryption_service=encryption_service,
        )
        result = await svc.enroll(user, db_session)
        secret = result["secret"]

        # Generate code for previous time step
        prev_time = int(datetime.now(timezone.utc).timestamp()) - 30
        prev_code = pyotp.TOTP(secret).at(prev_time)

        await svc.confirm(user, pyotp.TOTP(secret).now(), db_session)
        challenge = svc.create_challenge(user)
        token_service = MockTokenService()

        # Act
        token_pair = await svc.verify_and_issue(
            user, challenge, prev_code, token_service, db_session,
        )

        # Assert
        assert token_pair is not None

    async def test_verify_with_next_time_step(
        self,
        db_session: AsyncSession,
        settings: Settings,
    ) -> None:
        """GIVEN enrolled user, WHEN code from 30 s ahead, THEN accepted (valid_window=1)."""
        await _ensure_tables(settings)

        from app.models.tenant import Tenant
        from app.repositories.totp_secret_repository import TotpSecretRepository
        from app.services.totp_service import TotpService

        # Arrange
        tenant = Tenant(
            id=uuid.uuid4(),
            slug=f"nextstep-{uuid.uuid4().hex[:8]}",
            nombre="Next Step Test",
        )
        db_session.add(tenant)
        await db_session.flush()

        user = User(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            email_encrypted=encryption_service.encrypt("nextstep@example.com"),
            email_lookup=email_lookup_hash("nextstep@example.com"),
            password_hash=hash_password("x"),
            is_active=True,
            totp_enabled=False,
        )
        db_session.add(user)
        await db_session.flush()

        svc = TotpService(
            totp_repo=TotpSecretRepository(),
            encryption_service=encryption_service,
        )
        result = await svc.enroll(user, db_session)
        secret = result["secret"]

        # Generate code for next time step
        next_time = int(datetime.now(timezone.utc).timestamp()) + 30
        next_code = pyotp.TOTP(secret).at(next_time)

        await svc.confirm(user, pyotp.TOTP(secret).now(), db_session)
        challenge = svc.create_challenge(user)
        token_service = MockTokenService()

        # Act
        token_pair = await svc.verify_and_issue(
            user, challenge, next_code, token_service, db_session,
        )

        # Assert
        assert token_pair is not None

    async def test_confirm_with_previous_time_step(
        self,
        db_session: AsyncSession,
        settings: Settings,
    ) -> None:
        """GIVEN enrolled user, WHEN confirm with code from previous step, THEN accepted."""
        await _ensure_tables(settings)

        from app.models.tenant import Tenant
        from app.repositories.totp_secret_repository import TotpSecretRepository
        from app.services.totp_service import TotpService

        # Arrange
        tenant = Tenant(
            id=uuid.uuid4(),
            slug=f"confprev-{uuid.uuid4().hex[:8]}",
            nombre="Confirm Prev Step",
        )
        db_session.add(tenant)
        await db_session.flush()

        user = User(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            email_encrypted=encryption_service.encrypt("confprev@example.com"),
            email_lookup=email_lookup_hash("confprev@example.com"),
            password_hash=hash_password("x"),
            is_active=True,
            totp_enabled=False,
        )
        db_session.add(user)
        await db_session.flush()

        svc = TotpService(
            totp_repo=TotpSecretRepository(),
            encryption_service=encryption_service,
        )
        result = await svc.enroll(user, db_session)
        secret = result["secret"]

        # Generate code for previous time step
        prev_time = int(datetime.now(timezone.utc).timestamp()) - 30
        prev_code = pyotp.TOTP(secret).at(prev_time)

        # Act — confirm with previous step code
        confirmed = await svc.confirm(user, prev_code, db_session)

        # Assert
        assert confirmed is True
        assert user.totp_enabled is True

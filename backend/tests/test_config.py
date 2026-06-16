import os
from typing import Any

import pytest
from pydantic import ValidationError


class TestSettingsValid:
    def test_instantiates_with_valid_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@h:5432/db")
        monkeypatch.setenv("SECRET_KEY", "a" * 32)
        monkeypatch.setenv("ENCRYPTION_KEY", "b" * 32)
        monkeypatch.delenv("ACCESS_TOKEN_EXPIRE_MINUTES", raising=False)

        from app.core.config import Settings

        settings = Settings()
        assert settings.database_url == "postgresql+asyncpg://u:p@h:5432/db"
        assert len(settings.secret_key) >= 32
        assert len(settings.encryption_key) == 32
        assert settings.access_token_expire_minutes == 15

    def test_default_access_token_expire(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@h:5432/db")
        monkeypatch.setenv("SECRET_KEY", "a" * 32)
        monkeypatch.setenv("ENCRYPTION_KEY", "b" * 32)

        from app.core.config import Settings

        settings = Settings()
        assert settings.access_token_expire_minutes == 15


class TestSettingsInvalid:
    def test_fails_when_secret_key_too_short(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@h:5432/db")
        monkeypatch.setenv("SECRET_KEY", "short")
        monkeypatch.setenv("ENCRYPTION_KEY", "b" * 32)

        from app.core.config import Settings

        with pytest.raises(ValidationError):
            Settings()

    def test_fails_when_encryption_key_wrong_length(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@h:5432/db")
        monkeypatch.setenv("SECRET_KEY", "a" * 32)
        monkeypatch.setenv("ENCRYPTION_KEY", "short")

        from app.core.config import Settings

        with pytest.raises(ValidationError):
            Settings()

    def test_fails_when_access_token_not_int(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@h:5432/db")
        monkeypatch.setenv("SECRET_KEY", "a" * 32)
        monkeypatch.setenv("ENCRYPTION_KEY", "b" * 32)
        monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "not-an-int")

        from app.core.config import Settings

        with pytest.raises(ValidationError):
            Settings()

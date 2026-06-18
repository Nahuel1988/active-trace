from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="forbid",
    )

    database_url: str = Field(alias="DATABASE_URL")
    secret_key: str = Field(min_length=32, alias="SECRET_KEY")
    encryption_key: str = Field(min_length=32, max_length=32, alias="ENCRYPTION_KEY")
    access_token_expire_minutes: int = Field(default=15, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=7, alias="REFRESH_TOKEN_EXPIRE_DAYS")
    password_reset_expire_minutes: int = Field(default=15, alias="PASSWORD_RESET_EXPIRE_MINUTES")
    twofa_challenge_expire_minutes: int = Field(default=5, alias="TWOFA_CHALLENGE_EXPIRE_MINUTES")
    email_lookup_hmac_key: str = Field(min_length=16, alias="EMAIL_LOOKUP_HMAC_KEY")

    test_database_url: str | None = Field(default=None, alias="TEST_DATABASE_URL")

    otel_service_name: str = Field(default="activia-trace", alias="OTEL_SERVICE_NAME")
    otel_exporter_otlp_endpoint: str = Field(default="", alias="OTEL_EXPORTER_OTLP_ENDPOINT")

    @field_validator("encryption_key")
    @classmethod
    def encryption_key_must_be_32_chars(cls, v: str) -> str:
        if len(v) != 32:
            msg = f"ENCRYPTION_KEY must be exactly 32 characters, got {len(v)}"
            raise ValueError(msg)
        return v

FROM python:3.13-slim AS builder

WORKDIR /build
COPY pyproject.toml ./
RUN pip install --no-cache-dir \
    "fastapi>=0.115.0" \
    "uvicorn[standard]>=0.32.0" \
    "sqlalchemy[asyncio]>=2.0.36" \
    "alembic>=1.14.0" \
    "asyncpg>=0.30.0" \
    "pydantic>=2.10.0" \
    "pydantic-settings>=2.6.0" \
    "pyjwt>=2.9.0" \
    "argon2-cffi>=23.1.0" \
    "pyotp>=2.9.0" \
    "slowapi>=0.1.9" \
    "cryptography>=44.0.0" \
    "opentelemetry-api>=1.29.0" \
    "opentelemetry-sdk>=1.29.0" \
    "opentelemetry-instrumentation-fastapi>=0.50b0" \
    "opentelemetry-exporter-otlp-proto-http>=1.29.0"

FROM python:3.13-slim AS runtime

WORKDIR /app
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY app/ ./app/

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM runtime AS dev

RUN pip install --no-cache-dir \
    "pytest>=8.3.0" \
    "pytest-asyncio>=0.24.0" \
    "httpx>=0.28.0" \
    "pytest-cov>=6.0.0" \
    "email-validator>=2.0.0" \
    "python-multipart>=0.0.9"

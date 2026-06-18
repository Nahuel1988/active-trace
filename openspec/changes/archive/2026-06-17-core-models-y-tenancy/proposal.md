## Why

C-01 dejó el esqueleto de FastAPI corriendo con conexión a DB, pero sin ninguna entidad de dominio. Antes de construir cualquier módulo funcional (auth, estructura académica, padrón, etc.), el sistema necesita sus cimientos: el modelo `Tenant`, los mixins base con multi-tenancy y soft delete, un repositorio genérico que garantice aislamiento por tenant, y el helper de cifrado AES-256 para atributos PII. Sin estos pilares, cualquier modelo que se agregue tendría que reimplementar (o ignorar) las reglas más críticas del sistema.

## What Changes

- Nuevo modelo `Tenant` (entidad raíz del sistema multi-tenant).
- Mixin `TenantScopedMixin` con `id` (UUID v4), `tenant_id`, `created_at`, `updated_at`, `deleted_at` (soft delete); aplicable a toda entidad de dominio.
- `BaseRepository[T]` genérico con scope de tenant **siempre activo**: todo `SELECT` filtra por `tenant_id` por defecto; métodos `get`, `list`, `create`, `soft_delete`. Un query sin scope de tenant debe fallar en code review.
- Helper `EncryptionService` (AES-256-GCM) para cifrar/descifrar atributos `[cifrado]` (email, DNI, CUIL, CBU) en reposo; nunca expuestos en logs.
- `Migración 001: tenant` — tabla `tenant` en PostgreSQL.
- Convención de soft delete transversal: `deleted_at IS NULL` en todos los listados del repositorio base.
- Tests: aislamiento multi-tenant (usuario de tenant A no ve datos de tenant B), soft delete (registro marcado nunca aparece en listados), cifrado round-trip (cifrar → descifrar = valor original), timestamps automáticos.

## Capabilities

### New Capabilities

- `tenant-model`: Entidad `Tenant` (id, slug, nombre, activo, timestamps). Raíz de todo el árbol de datos del sistema.
- `base-mixin`: Mixin SQLAlchemy con UUID PK, `tenant_id` (FK → Tenant), `created_at`, `updated_at`, `deleted_at` para soft delete.
- `tenant-scoped-repository`: Repositorio base genérico parametrizado por modelo. Aplica `WHERE tenant_id = :tenant_id` y `WHERE deleted_at IS NULL` en todas las consultas por defecto.
- `encryption-pii`: Servicio de cifrado/descifrado AES-256-GCM sobre la `ENCRYPTION_KEY` de Settings. Usado para columnas `[cifrado]` en modelos futuros.

### Modified Capabilities

<!-- sin cambios a specs existentes en esta etapa -->

## Impact

- `backend/app/models/base.py` — mixin base (a crear)
- `backend/app/models/tenant.py` — modelo Tenant (a crear)
- `backend/app/repositories/base.py` — BaseRepository genérico (a crear)
- `backend/app/core/security.py` — agregar EncryptionService AES-256-GCM
- `backend/app/core/tenancy.py` — contexto de tenant para DI (expandir)
- `backend/alembic/versions/001_tenant.py` — migración inicial (a crear)
- `backend/tests/` — tests de aislamiento, soft delete, cifrado, timestamps
- Dependencia nueva: `cryptography` (ya en pyproject.toml si está listada, confirmar)

## Context

C-01 entregó la base: FastAPI async, SQLAlchemy `Base`, motor y sesión inyectados vía DI, `docker-compose.yml` con Postgres y Alembic configurado. Lo que falta es el primer nivel del modelo de dominio: la entidad `Tenant`, el mixin que convierte cualquier tabla futura en "tenant-aware", un repositorio base que aplique ese scope automáticamente, y el helper de cifrado para los atributos PII. Todo módulo funcional posterior (auth, estructura académica, padrón, etc.) depende de estos cuatro pilares.

El sistema es **multi-tenant row-level** (ADR-002 cerrada): una sola base de datos, columna `tenant_id` en cada tabla de dominio, repositories que filtran por tenant por defecto. No hay base de datos por tenant.

## Goals / Non-Goals

**Goals:**

- Entidad `Tenant` persistida en PostgreSQL (migración 001).
- Mixin `TenantScopedMixin` aplicable a cualquier modelo SQLAlchemy futuro.
- `BaseRepository[T]` genérico con scope de tenant + soft delete automáticos.
- `EncryptionService` AES-256-GCM para cifrar/descifrar valores en reposo.
- Tests de aislamiento multi-tenant, soft delete, cifrado round-trip y timestamps.

**Non-Goals:**

- Endpoints HTTP para CRUD de Tenant (llegan en cambios posteriores de admin).
- Configuración por tenant (branding, plantillas, flags): escapa al scope de C-02.
- Modelos de dominio más allá de `Tenant` (Usuario, Carrera, etc.).
- Rotación de claves de cifrado (complejidad operacional fuera del MVP inicial).
- Tests de carga o performance de queries.

## Decisions

### D-01 — Mixin via `MappedColumn` de SQLAlchemy 2.0 (sin `declared_attr` heredado)

SQLAlchemy 2.0 permite definir mixins con `Mapped[T]` y `mapped_column(...)` directamente, sin necesidad de envolver con `declared_attr`. Es más legible, type-safe, y consistente con el estilo del proyecto.

Alternativa descartada: `declared_attr` de SQLAlchemy 1.x — más verboso, no agrega valor en SA 2.0.

### D-02 — UUID v4 como PK generada en Python (no en DB)

Generación con `uuid.uuid4()` vía `default=uuid.uuid4` en `mapped_column`. Evita dependencia de funciones DB-específicas y permite conocer el ID antes de insertar (útil para audit log y tests deterministas).

Alternativa descartada: `gen_random_uuid()` de PostgreSQL — acopla la generación al motor y complica el testing.

### D-03 — Soft delete con columna `deleted_at: datetime | None`

`None` = registro activo; timestamp = eliminado. El repositorio base aplica `WHERE deleted_at IS NULL` en todos los listados por defecto. Para recuperación o auditoría, se exponen métodos explícitos (`list_including_deleted`).

Alternativa descartada: columna booleana `is_deleted` — no registra cuándo se eliminó, lo que empobrece la traza de auditoría.

### D-04 — AES-256-GCM sobre AES-256-CBC

GCM provee cifrado autenticado: detecta manipulación del ciphertext (integridad + confidencialidad). CBC solo ofrece confidencialidad y requiere padding. GCM es el estándar recomendado para datos en reposo cuando no se usa padding.

Implementación: `cryptography.hazmat.primitives.ciphers.aead.AESGCM`. IV aleatorio de 12 bytes generado por cifrado, antepuesto al ciphertext (IV || ciphertext), codificado en base64 para almacenamiento textual.

### D-05 — `BaseRepository[T]` inyecta `tenant_id` desde parámetro explícito (no contextvars)

El `tenant_id` llega al repositorio como argumento en cada método (`get`, `list`, etc.), obtenido desde el JWT verificado vía dependency injection de FastAPI. Se descartó el uso de `contextvars` porque dificulta el testing y oculta el flujo de datos.

### D-06 — Migración 001 crea solo la tabla `tenant` sin seed

El seed de datos de tenant inicial es responsabilidad de scripts de deployment o fixtures de test, no de la migración. Mantiene las migraciones idempotentes y deterministas en cualquier entorno.

## Risks / Trade-offs

- **Olvidar `TenantScopedMixin` en un modelo futuro** → El repositorio base requiere `tenant_id` explícitamente; el type checker capturará el error si el modelo no tiene el atributo. Code review es el safety net final.

- **`BaseRepository` no cubre queries complejos** (JOINs, subqueries) → Diseño intencional: los repos especializados heredan de `BaseRepository` y agregan sus propios métodos. No es un ORM completo, sino un núcleo seguro.

- **IV repetido en cifrado** → `AESGCM` con IV de 12 bytes generado aleatoriamente con `os.urandom(12)` tiene probabilidad negligible de colisión en el volumen de datos esperado. Para volúmenes masivos (>2^32 registros), se reevalúa.

- **Rotación de `ENCRYPTION_KEY`** → No está en scope de C-02. Los valores cifrados con la clave anterior quedan ilegibles si se rota sin re-cifrado. Se debe documentar como deuda operacional.

## Migration Plan

1. Aplicar `alembic upgrade head` en entorno de dev (solo crea tabla `tenant`).
2. No hay rollback destructivo: `alembic downgrade -1` elimina la tabla `tenant` (sin datos de producción en este punto).
3. En producción futura: la tabla se crea vacía; el seed de tenant inicial se aplica por script separado.

## Open Questions

- ¿El `Tenant` necesita columna `config: JSONB` desde ya para configuración por tenant? → Se reserva para C-03 o posterior cuando la configuración sea necesaria. Por ahora, schema mínimo.

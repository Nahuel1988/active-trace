## Context

C-02 dejó disponible: modelo `Tenant`, `BaseMixin` (UUID `id`, `tenant_id`, `created_at`, `updated_at`, `deleted_at`), `BaseRepository[T]` con scope de tenant obligatorio + soft delete, y `EncryptionService` AES-256-GCM. La migración existente es `001_tenant`. **No existe modelo `User`.**

Este change implementa ADR-001 (auth propio, cerrada): email + password (Argon2id), JWT access 15 min + refresh con rotación, 2FA TOTP opcional, recuperación con token de un solo uso, rate limiting de login y la dependency `get_current_user`. Restricciones del proyecto que constriñen el diseño:

- **Regla de oro**: identidad, tenant y roles SOLO del JWT verificado server-side. Ningún parámetro de URL/body/header puede alterarlos.
- **Clean Architecture estricta**: Routers → Services → Repositories → Models. Sin lógica de negocio en routers, sin SQL en services.
- **Multi-tenant row-level**: `tenant_id` en toda tabla nueva; repositories filtran por tenant.
- **Soft delete siempre**, `extra='forbid'` en todos los schemas Pydantic, ≤500 LOC/archivo, **una migración por cambio de schema** (`002`), tests sin mocks de DB.
- **Governance CRÍTICO**: requiere aprobación humana antes de implementar.

## Goals / Non-Goals

**Goals:**
- Modelo `User` con identidad por UUID, email PII cifrado, password Argon2id, legajo como atributo de negocio (nunca credencial/selector).
- Endpoints: login, refresh (rotación + detección de reuso), logout, 2FA enroll/confirm/verify, forgot, reset.
- Dependency `get_current_user` como única fuente de identidad del sistema.
- Rate limiting de login 5/60s por IP+email, fail-closed.
- Secret TOTP cifrado AES-256 en reposo; tokens (refresh, reset) persistidos solo como **hash**, nunca en claro.
- Migración Alembic `002` con todas las tablas de auth.

**Non-Goals:**
- RBAC fino `require_permission` y matriz rol×permiso administrable → **C-04** (este change solo asocia roles al usuario y los embebe como claim).
- Impersonación (ADR-004) → se difiere.
- Moodle SSO de alumnos → Fase 2.
- Audit log de eventos de auth → **C-05** (se dejan hooks/puntos de extensión, pero no se implementa el log aquí).
- CSRF y endurecimiento de cabeceras transversales → fuera de scope de este change.

## Decisions

### D1 — Modelo `User` se introduce en este change
C-02 no entregó `User`. El módulo de auth lo requiere, así que se crea aquí. Hereda `BaseMixin` (UUID, tenant_id, soft delete, timestamps).

- `email`: PII. Se persiste **cifrado** (`EncryptionService`, AES-256-GCM) en `email_encrypted`, y además una columna **`email_lookup`** con hash determinístico (HMAC-SHA256 con clave dedicada) + `UNIQUE(tenant_id, email_lookup)` para permitir búsqueda por login sin descifrar y garantizar unicidad por tenant. (AES-GCM es no determinístico → no sirve para buscar; por eso el hash de lookup separado.)
- `password_hash`: Argon2id (`argon2-cffi`). Nunca texto plano.
- `legajo`: nullable, atributo de negocio. **No** es PK, ni credencial, ni selector de sesión.
- `is_active`: bool. Un usuario inactivo o soft-deleted no puede autenticarse.
- Roles vía tabla puente `user_role` (M:N con `role`). El catálogo `role` es data; la matriz rol×permiso administrable es C-04.

**Alternativa descartada**: email en claro indexado → viola la regla de PII cifrada AES-256.

### D2 — Hashing de passwords: Argon2id
Regla dura del proyecto y ADR-001. `argon2-cffi` con parámetros por defecto seguros (memoria/tiempo configurables vía Settings). `verify` + soporte de `needs_rehash` para upgrades futuros.

### D3 — JWT: access 15 min + refresh con rotación, claims mínimos
- Librería: **PyJWT** (HS256 con `SECRET_KEY`). Simple, sin dependencias de criptografía asimétrica innecesaria a esta escala.
- Access token: claims mínimos `sub` (user_id UUID), `tenant_id`, `roles` (lista), `exp`, `iat`, `type=access`. **Sin permisos** (se resuelven server-side en C-04).
- Refresh token: opaco (string aleatorio de alta entropía), persistido en DB **solo como hash** (`refresh_token` tabla), con `expires_at` y `revoked_at`. El refresh NO es un JWT — así su revocación es real (stateful), no solo expiración.

### D4 — Refresh rotation con familia de tokens (detección de reuso)
Cada refresh pertenece a una **familia** (`family_id`). Al refrescar:
1. Se busca el hash del refresh presentado entre los no revocados y no vencidos del tenant.
2. Si **no existe pero pertenece a una familia conocida ya rotada** (reuso de un token ya consumido) → se interpreta como robo: se **revoca la familia completa** y se rechaza (401).
3. Si es válido: se marca `revoked_at` en el actual (rotación = single-use) y se emite uno nuevo en la misma familia.

`logout` revoca la familia activa del usuario. Esto satisface "refresh usado se invalida" y "reuso invalida".

**Alternativa descartada**: refresh como JWT con sola expiración → no permite revocación real (logout no podría invalidar antes de `exp`).

### D5 — 2FA TOTP como gate entre credenciales y emisión de sesión
- Librería: **pyotp**. Secret base32 generado en enroll, **cifrado AES-256** (`EncryptionService`) en `totp_secret.secret_encrypted`, con `confirmed_at` (enrolamiento en dos pasos: enroll genera + devuelve `otpauth://` URI para QR; confirm valida primer código y activa).
- Login con 2FA habilitada: tras validar password, **NO** se emite el par de tokens. Se devuelve un **challenge** firmado de vida muy corta (JWT `type=2fa_challenge`, ~5 min, claims `sub`+`tenant_id`) que el cliente presenta a `POST /api/auth/2fa/verify` junto con el código TOTP. Solo al verificar se emite el par access+refresh.
- Ventana de tolerancia ±1 step (30s) para drift de reloj.

**Máquina de estados de login:**
```
login(email, password)
   │ credenciales inválidas → 401 (mensaje uniforme)
   │ usuario inactivo/eliminado → 401 (uniforme)
   ▼ credenciales OK
   ├── 2FA deshabilitada → emitir {access, refresh}            [SESIÓN]
   └── 2FA habilitada   → emitir {challenge_2fa}               [PENDIENTE]
                              │
                              ▼ 2fa/verify(challenge, code)
                              ├── code inválido → 401
                              └── code OK → emitir {access, refresh}  [SESIÓN]
```

### D6 — Recuperación: token de un solo uso, respuesta uniforme
- `forgot(email)`: SIEMPRE responde 200 con cuerpo uniforme (no revela si el email existe). Si existe, genera token aleatorio, persiste **solo su hash** en `password_reset_token` con `expires_at` corto (15 min) y dispara el envío por email (el envío real se delega al worker/integración; aquí se deja el punto de extensión).
- `reset(token, new_password)`: valida token (existe, no usado, no vencido), setea nueva password Argon2id, marca `used_at`, e **invalida todas las sesiones activas** del usuario (revoca familias). Un token usado o vencido → 400.

### D7 — Rate limiting: 5/60s por IP+email en login
- Implementación: **SlowAPI** (limiter sobre Starlette) con backend **in-memory** para el MVP single-instance, key = `ip + ":" + email`. Diseñado detrás de una interfaz para poder migrar a **Redis** cuando haya múltiples instancias.
- Superado el límite → **429** (fail-closed). El conteo se aplica antes de tocar la DB de credenciales.

**Trade-off**: in-memory no es compartido entre réplicas; aceptable en MVP, documentado como riesgo (R3).

### D8 — `get_current_user` dependency
Función FastAPI dependency en `app/core/dependencies.py`:
1. Extrae el Bearer token del header `Authorization`.
2. Decodifica y **verifica** firma + `exp` + `type=access` con `SECRET_KEY`. Falla → 401.
3. Toma `sub` (user_id) y `tenant_id` **del token verificado** — NUNCA de la URL/body.
4. Carga el `User` vía `UserRepository.get(id=sub, tenant_id=claim_tenant)` (tenant-scoped). Si no existe / inactivo / soft-deleted → 401.
5. Devuelve un objeto `CurrentUser` inmutable (`user_id`, `tenant_id`, `roles`).

Cualquier `id` que llegue en la petición es dato de negocio a validar contra esta identidad, jamás la reemplaza.

### D9 — Capa y archivos (Clean Architecture)
```
app/
├── models/
│   ├── user.py                 # User (BaseMixin)
│   ├── role.py                 # Role, user_role (puente)
│   ├── refresh_token.py        # RefreshToken (hash, family_id, expires_at, revoked_at)
│   ├── totp_secret.py          # TotpSecret (secret_encrypted, confirmed_at)
│   └── password_reset_token.py # PasswordResetToken (token_hash, expires_at, used_at)
├── schemas/auth.py             # Pydantic v2, extra='forbid'
├── repositories/
│   ├── user_repository.py
│   ├── refresh_token_repository.py
│   ├── totp_secret_repository.py
│   └── password_reset_token_repository.py
├── services/
│   ├── auth_service.py         # login, logout (orquesta)
│   ├── token_service.py        # emisión/rotación JWT + refresh
│   ├── totp_service.py         # enroll/confirm/verify
│   └── password_reset_service.py
├── core/
│   ├── security.py             # JWT encode/decode, Argon2 hash/verify, email lookup hash
│   ├── dependencies.py         # get_current_user, get_db
│   └── rate_limit.py           # limiter interface (SlowAPI in-memory)
└── api/v1/routers/auth.py      # solo transporte + validación, llama a services
alembic/versions/002_*.py       # user, role, user_role, refresh_token, totp_secret, password_reset_token
```
Ningún archivo supera 500 LOC; si `auth_service` crece, se parte por sub-flujo.

### D10 — Modelo de datos (tablas nuevas, todas con `tenant_id` salvo `role` global por tenant)
| Tabla | Columnas clave |
|-------|----------------|
| `user` | `id` UUID PK, `tenant_id` FK, `email_encrypted`, `email_lookup` (UNIQUE con tenant_id), `password_hash`, `legajo` (nullable), `is_active`, `totp_enabled`, + BaseMixin |
| `role` | `id` UUID PK, `tenant_id` FK, `code` (UNIQUE con tenant_id), `nombre`, + BaseMixin |
| `user_role` | `user_id` FK, `role_id` FK, `tenant_id` FK, PK compuesta; vigencia (`desde`,`hasta` nullable) |
| `refresh_token` | `id` UUID PK, `tenant_id` FK, `user_id` FK, `token_hash` (UNIQUE), `family_id` UUID, `expires_at`, `revoked_at` (nullable) |
| `totp_secret` | `id` UUID PK, `tenant_id` FK, `user_id` FK (UNIQUE), `secret_encrypted`, `confirmed_at` (nullable) |
| `password_reset_token` | `id` UUID PK, `tenant_id` FK, `user_id` FK, `token_hash` (UNIQUE), `expires_at`, `used_at` (nullable) |

`vigencia` en `user_role` materializa §5 de actores y roles (asignaciones con desde/hasta). Soft delete vía `deleted_at` heredado.

## Risks / Trade-offs

- **[R1] Email cifrado no determinístico impide buscar por login]** → columna `email_lookup` con HMAC determinístico + UNIQUE(tenant_id, email_lookup); el cifrado real queda en `email_encrypted`.
- **[R2] Refresh como JWT no es revocable]** → refresh opaco persistido como hash en DB con `family_id`; rotación single-use + revocación de familia ante reuso.
- **[R3] Rate limit in-memory no se comparte entre réplicas]** → interfaz abstracta para migrar a Redis; documentado; aceptable en MVP single-instance.
- **[R4] Enumeración de cuentas en forgot/login]** → respuestas uniformes (mismo cuerpo y status) existan o no la cuenta; mismo tiempo de respuesta cuando sea factible.
- **[R5] Robo de refresh token]** → detección de reuso revoca la familia completa (D4).
- **[R6] Secret TOTP en reposo]** → cifrado AES-256 vía EncryptionService; nunca en logs.
- **[R7] Tokens de reset filtrados en logs]** → solo se persiste el hash; el token en claro vive únicamente en el email y la request de reset.
- **[R8] Drift de reloj en TOTP]** → ventana ±1 step (30s).

## Migration Plan

- **Migración `002`** (una sola, por la regla de migración por cambio de schema): crea `user`, `role`, `user_role`, `refresh_token`, `totp_secret`, `password_reset_token` con sus FKs a `tenant.id`, índices únicos y columnas BaseMixin.
- **Rollback**: `alembic downgrade` de `002` elimina las seis tablas en orden inverso de dependencias.
- **Datos**: no hay seed de usuarios en este change (la provisión del primer ADMIN del tenant es FL-12 / otro change). Sin migración de datos previa.

## Open Questions

- **OQ-1**: Backend definitivo del rate limit (in-memory vs Redis) para producción multi-réplica → se cierra al definir el deploy (default in-memory para MVP).
- **OQ-2**: Canal de envío del email de recuperación (worker propio vs N8N, ADR-003) → este change deja el punto de extensión; el envío real se conecta al construir comunicaciones. Para tests, se inyecta un sender fake.
- **OQ-3**: ¿`role` por tenant o catálogo global? → se modela por tenant (UNIQUE por tenant_id) para permitir catálogo administrable por institución (§2 actores y roles); confirmar con C-04.

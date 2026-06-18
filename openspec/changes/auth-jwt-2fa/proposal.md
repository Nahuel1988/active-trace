## Why

C-02 entregó los cimientos de datos (modelo `Tenant`, `BaseMixin`, `BaseRepository` con scope de tenant, `EncryptionService` AES-256) pero **no existe aún ninguna identidad de usuario ni mecanismo de acceso**. Sin autenticación no hay forma segura de operar el sistema: todo módulo posterior del producto (calificaciones, comunicación, equipos, liquidaciones, auditoría) depende de poder resolver *quién* es el actor, *qué tenant* tiene y *qué roles* posee — y de hacerlo, según la regla de oro del dominio, **exclusivamente desde una sesión verificada**, nunca desde un parámetro de la petición.

Este change construye la capa de autenticación endurecida definida en ADR-001 (auth propio, cerrada): email + password (Argon2id), JWT access de vida corta + refresh con rotación, 2FA TOTP opcional, recuperación de contraseña con token de un solo uso, rate limiting de login, y la dependency `get_current_user` que materializa la regla de oro de identidad para todo el resto del sistema.

> **Governance: CRÍTICO.** Este módulo (auth) es uno de los dominios de máxima criticidad. La propuesta y el diseño se entregan para **revisión y aprobación humana explícita antes de implementar**. Ningún código de este change debe escribirse sin esa aprobación.

## What Changes

- **Modelo `User`** (nuevo): identidad por UUID interno, `tenant_id`, `email` (PII cifrada AES-256 + columna de búsqueda determinística), `password_hash` (Argon2id), `legajo` opcional (atributo de negocio, **nunca** credencial ni selector de sesión), flags de estado, soft delete heredado de `BaseMixin`. Relación con roles (catálogo rol × permiso es data, no código).
- **`POST /api/auth/login`** — valida email + password con Argon2id; si el usuario tiene 2FA habilitada, NO emite sesión: devuelve un challenge de 2FA. Si no, emite el par JWT access (15 min) + refresh (rotación). Claims mínimos: `sub` (user_id), `tenant_id`, `roles`, `exp`.
- **`POST /api/auth/2fa/verify`** — segundo factor TOTP; gate entre la validación de credenciales y la emisión de la sesión. Solo tras superarlo se emite el par de tokens.
- **`POST /api/auth/2fa/enroll`** + **`POST /api/auth/2fa/confirm`** — enrolamiento TOTP opcional por usuario (genera secret cifrado AES-256, devuelve URI para QR, confirma con el primer código válido).
- **`POST /api/auth/refresh`** — rota el refresh token (el usado se invalida inmediatamente) y emite un nuevo par. El **reuso de un refresh ya rotado revoca toda la familia de tokens** (detección de robo).
- **`POST /api/auth/logout`** — revoca la sesión (refresh token actual y su familia).
- **`POST /api/auth/forgot`** — genera un token de un solo uso con expiración corta y lo entrega por email (respuesta uniforme, no revela si el email existe).
- **`POST /api/auth/reset`** — valida el token de reset (un solo uso, no vencido), setea nueva password con Argon2id e invalida el token y las sesiones activas.
- **Rate limiting** — 5 intentos / 60s por combinación IP + email en `login` (fail-closed: superado el límite → 429).
- **Dependency `get_current_user`** — decodifica y verifica el JWT, resuelve identidad + `tenant_id` + roles **del token verificado**, carga el `User` activo del tenant. Es la única fuente de identidad del sistema.
- **Migración Alembic `002`** — tablas `user`, `role`, `user_role`, `refresh_token`, `totp_secret`, `password_reset_token`.

## Capabilities

### New Capabilities
- `user-identity`: Modelo `User` con identidad por UUID interno, email PII cifrado, password hash Argon2id, legajo como atributo de negocio (no credencial), roles asociados, soft delete y scope de tenant.
- `auth-session`: Login con email+password, emisión de JWT access (15 min) + refresh con rotación, logout/revocación, claims mínimos y la dependency `get_current_user` que resuelve identidad/tenant/roles exclusivamente desde el token verificado (regla de oro).
- `auth-2fa`: Segundo factor TOTP opcional por usuario — enrolamiento, confirmación y verificación como gate entre credenciales válidas y emisión de sesión; secret cifrado AES-256 en reposo.
- `auth-recovery`: Recuperación de contraseña con token de un solo uso y expiración corta (forgot/reset), respuesta uniforme que no filtra existencia de cuentas, invalidación tras uso o vencimiento.
- `auth-rate-limit`: Limitación de tasa en login (5/60s por IP+email) fail-closed para mitigar fuerza bruta.

### Modified Capabilities
<!-- Ninguna. C-02 entregó tenant-model, base-mixin, tenant-scoped-repository y encryption-pii; este change los CONSUME (no cambia sus requisitos): User hereda BaseMixin, usa EncryptionService para el email PII y se accede vía BaseRepository tenant-scoped. -->

## Impact

- **Código nuevo**: `app/models/user.py`, `role.py`, `refresh_token.py`, `totp_secret.py`, `password_reset_token.py`; `app/schemas/auth.py`; `app/repositories/{user,refresh_token,totp_secret,password_reset_token}_repository.py`; `app/services/{auth,token,totp,password_reset}_service.py`; `app/api/v1/routers/auth.py`; `app/core/security.py` (JWT + Argon2), `app/core/dependencies.py` (`get_current_user`), `app/core/rate_limit.py`; `alembic/versions/002_*.py`.
- **Dependencias nuevas**: `python-jose` o `pyjwt` (JWT), `argon2-cffi` (Argon2id), `pyotp` (TOTP), librería de rate limiting (SlowAPI o equivalente in-memory/Redis — decisión en design).
- **Consume de C-02**: `BaseMixin` (UUID, tenant_id, timestamps, soft delete), `EncryptionService` (email PII, secret TOTP), `BaseRepository` (scope de tenant).
- **Habilita a TODO el resto del sistema**: `get_current_user` y el futuro `require_permission` (C-04 RBAC) son la base de autenticación/autorización de cada endpoint posterior. C-04 (rbac) depende directamente de este change.
- **Sin cambios de comportamiento previos**: no rompe nada de C-01/C-02; es aditivo.

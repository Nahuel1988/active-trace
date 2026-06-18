# Tasks — auth-jwt-2fa (C-03)

> **Governance: CRÍTICO.** No iniciar implementación sin aprobación humana explícita del proposal + design.
> **TDD estricto** en cada task: RED (test que falla) → GREEN (código mínimo) → TRIANGULATE (2do+ caso / edge) → REFACTOR.
> **Tests sin mocks de DB**: base real / contenedor efímero. Cobertura ≥80% líneas, ≥90% reglas de negocio.
> Consume de C-02: `BaseMixin`, `BaseRepository`, `EncryptionService`. No re-implementar.

## 0. Setup y dependencias

- [x] 0.1 Agregar dependencias backend: `pyjwt`, `argon2-cffi`, `pyotp`, `slowapi` (rate limit). Fijar versiones.
- [x] 0.2 Extender `core/config.py` Settings con `ACCESS_TOKEN_EXPIRE_MINUTES` (default 15), `REFRESH_TOKEN_EXPIRE_DAYS`, `PASSWORD_RESET_EXPIRE_MINUTES` (15), `TWOFA_CHALLENGE_EXPIRE_MINUTES` (5), `EMAIL_LOOKUP_HMAC_KEY`. Test: arranque falla si falta `SECRET_KEY`/`EMAIL_LOOKUP_HMAC_KEY`.

## 1. core/security — primitivas (TDD)

- [x] 1.1 RED→GREEN→TRIANGULATE: `hash_password`/`verify_password` (Argon2id). Casos: hash con prefijo `$argon2id$`, verify correcta=true, verify incorrecta=false, password en claro nunca en el hash.
- [x] 1.2 RED→GREEN→TRIANGULATE: `encode_access_token`/`decode_token` (PyJWT HS256). Casos: claims mínimos presentes (`sub`,`tenant_id`,`roles`,`exp`,`iat`,`type`), exp=15min, firma manipulada→error, token vencido→error, type incorrecto→error.
- [x] 1.3 RED→GREEN→TRIANGULATE: `email_lookup_hash` (HMAC-SHA256 determinístico). Casos: mismo email→mismo hash, emails distintos→hashes distintos, normalización (trim/lowercase).
- [x] 1.4 RED→GREEN→TRIANGULATE: generadores de token opaco (`generate_opaque_token` + `hash_token`) para refresh y reset. Casos: alta entropía, hash determinístico, token en claro ≠ hash.
- [x] 1.5 REFACTOR: extraer constantes, limpiar duplicación; tests verdes tras cada paso. Verificar ≤500 LOC.

## 2. Modelos + migración 002 (TDD)

- [x] 2.1 RED→GREEN: modelo `User` (hereda BaseMixin) con `email_encrypted`, `email_lookup`, `password_hash`, `legajo` nullable, `is_active`, `totp_enabled`. Test: persistencia con UUID + tenant_id + timestamps; FK a tenant inexistente falla.
- [x] 2.2 TRIANGULATE: email cifrado en DB (columna no contiene claro), `UNIQUE(tenant_id, email_lookup)` (duplicado mismo tenant falla; mismo email en otro tenant OK).
- [x] 2.3 RED→GREEN→TRIANGULATE: modelos `Role` (`code` único por tenant) y `user_role` (puente con `tenant_id`, `desde`, `hasta` nullable). Test: roles efectivos = unión de vigentes; asignación vencida excluida pero persiste histórico.
- [x] 2.4 RED→GREEN: modelo `RefreshToken` (`token_hash` UNIQUE, `family_id`, `expires_at`, `revoked_at`). Test: persistencia + scope tenant.
- [x] 2.5 RED→GREEN: modelo `TotpSecret` (`user_id` UNIQUE, `secret_encrypted`, `confirmed_at`). Test: secret cifrado en DB (no claro).
- [x] 2.6 RED→GREEN: modelo `PasswordResetToken` (`token_hash` UNIQUE, `expires_at`, `used_at`). Test: token_hash persistido como hash, no claro.
- [x] 2.7 Crear migración Alembic `002` (una sola) con las 6 tablas, FKs, índices únicos, columnas BaseMixin. Test: `alembic upgrade head` desde 001 crea todas las tablas; `downgrade` las elimina en orden.

## 3. Repositories tenant-scoped (TDD)

- [x] 3.1 RED→GREEN→TRIANGULATE: `UserRepository` sobre `BaseRepository` + `get_by_email_lookup(tenant_id, email_lookup)`. Casos: encuentra usuario del tenant; no encuentra de otro tenant; excluye soft-deleted/inactivo.
- [x] 3.2 RED→GREEN→TRIANGULATE: `RefreshTokenRepository`: crear, `get_by_hash`, `revoke(id)`, `revoke_family(family_id, tenant_id)`. Casos: aislamiento de tenant en cada método.
- [x] 3.3 RED→GREEN: `TotpSecretRepository`: `get_by_user`, upsert de enroll, marcar confirmado.
- [x] 3.4 RED→GREEN: `PasswordResetTokenRepository`: crear, `get_by_hash`, marcar usado.

## 4. Schemas Pydantic (TDD, extra='forbid')

- [x] 4.1 RED→GREEN→TRIANGULATE: schemas de request/response de auth (`LoginRequest`, `TokenPair`, `RefreshRequest`, `LogoutRequest`, `TwoFAEnrollResponse`, `TwoFAConfirmRequest`, `TwoFAVerifyRequest`, `ForgotRequest`, `ResetRequest`). Casos: validación de email/password; campo extra → 422 (`extra='forbid'`); response no expone PII ni hashes.

## 5. token_service — emisión y rotación (TDD) [auth-session]

- [x] 5.1 RED→GREEN: `issue_token_pair(user)` emite access (claims mínimos, 15min) + refresh (opaco, hash persistido con family_id). Test: par válido emitido, refresh persistido como hash.
- [x] 5.2 RED→GREEN→TRIANGULATE: `rotate_refresh(token)`: válido → revoca usado + emite nuevo en misma familia; vencido → 401. Casos happy + vencido.
- [x] 5.3 RED→GREEN→TRIANGULATE: detección de reuso: presentar refresh ya rotado → revoca familia completa + rechaza. Casos: reuso simple; tras reuso ningún token de la familia sirve.
- [x] 5.4 RED→GREEN: `revoke_session`/logout revoca familia activa. Test: refresh posterior con ese token → 401.

## 6. auth_service + get_current_user (TDD) [auth-session]

- [x] 6.1 RED→GREEN→TRIANGULATE: `authenticate(email, password, tenant)`: credenciales OK (sin 2FA)→user; password incorrecta→error uniforme; email inexistente→mismo error uniforme; usuario inactivo/soft-deleted→error.
- [x] 6.2 RED→GREEN: login orquesta authenticate→ si 2FA off `issue_token_pair`. Test integración endpoint `POST /api/auth/login` 200 con par.
- [x] 6.3 RED→GREEN→TRIANGULATE: `get_current_user` dependency. Casos: token válido→identidad del token; **parámetro de URL/body distinto al token → se ignora, usa el token** (identidad inmutable); firma inválida→401; vencido→401; usuario inexistente/inactivo→401.
- [x] 6.4 RED→GREEN: endpoints `POST /api/auth/refresh` y `POST /api/auth/logout` cableados a token_service (routers sin lógica de negocio).
- [x] 6.5 REFACTOR: partir auth_service si supera 500 LOC; tests verdes.

## 7. totp_service + 2FA gate (TDD) [auth-2fa]

- [x] 7.1 RED→GREEN: `enroll(user)` genera secret, lo cifra AES-256, persiste no confirmado, devuelve URI `otpauth://`. Test: secret cifrado en DB; `totp_enabled` sigue false.
- [x] 7.2 RED→GREEN→TRIANGULATE: `confirm(user, code)`: código válido→`confirmed_at`+`totp_enabled=true`; inválido→400, sigue false.
- [x] 7.3 RED→GREEN→TRIANGULATE: gate en login: usuario con 2FA → login devuelve challenge (`type=2fa_challenge`, 5min), NO emite par. `2fa/verify` con código válido→emite par; código inválido→401; challenge vencido→401.
- [x] 7.4 TRIANGULATE: tolerancia drift ±1 step — código del step anterior aceptado.
- [x] 7.5 Cablear endpoints `POST /api/auth/2fa/enroll`, `/2fa/confirm`, `/2fa/verify`.

## 8. password_reset_service (TDD) [auth-recovery]

- [x] 8.1 RED→GREEN→TRIANGULATE: `forgot(email)`: email existente→genera token (hash persistido, exp 15min) + dispara sender (inyectado, fake en test); respuesta uniforme 200. Email inexistente→mismo 200, sin token. Token en DB solo como hash.
- [x] 8.2 RED→GREEN→TRIANGULATE: `reset(token, new_password)`: válido→nueva password Argon2id + `used_at` + revoca sesiones; usado→400; vencido→400; inválido→400.
- [x] 8.3 TRIANGULATE: login con nueva password tras reset OK; password vieja inválida.
- [x] 8.4 Cablear endpoints `POST /api/auth/forgot` y `POST /api/auth/reset`.

## 9. Rate limiting de login (TDD) [auth-rate-limit]

- [x] 9.1 RED→GREEN: interfaz de rate limit (in-memory SlowAPI, key=IP+email) inyectable. 
- [x] 9.2 RED→GREEN→TRIANGULATE: aplicar a `login`. Casos: ≤5/60s procesan; 6º→429 sin tocar credenciales; email distinto→contador propio; ventana reinicia tras 60s.

## 10. Integración E2E y cierre

- [ ] 10.1 Test E2E flujo completo: login OK→refresh (rotación)→reuso del viejo→familia revocada→logout.
- [ ] 10.2 Test E2E: enroll 2FA→confirm→login con challenge→verify→sesión.
- [ ] 10.3 Test E2E: forgot→reset→login con nueva password.
- [ ] 10.4 Test multi-tenant: usuario de tenant A nunca autentica/resuelve identidad de tenant B (aislamiento en login, get_current_user y todos los repos).
- [ ] 10.5 Verificar cobertura ≥80% líneas / ≥90% reglas de negocio. Verificar ≤500 LOC por archivo backend.
- [ ] 10.6 Code review de seguridad: ningún query sin scope de tenant; identidad solo del JWT; sin PII/tokens en logs; schemas `extra='forbid'`; soft delete respetado.

## ADDED Requirements

### Requirement: Enrolamiento TOTP opcional por usuario
El sistema SHALL exponer `POST /api/auth/2fa/enroll` que genere un secret TOTP base32 para el usuario autenticado, lo persista cifrado AES-256 (vía `EncryptionService`) en `totp_secret.secret_encrypted` con `confirmed_at = null`, y devuelva una URI `otpauth://` para generar el QR. El secret NUNCA MUST persistirse ni registrarse en texto plano.

#### Scenario: Enroll genera secret cifrado y URI
- **WHEN** un usuario autenticado solicita enrolar 2FA
- **THEN** el sistema persiste el secret cifrado (la columna no contiene el secret en claro) y responde con una URI `otpauth://`

#### Scenario: Secret aún no confirmado no habilita 2FA
- **WHEN** un usuario enroló pero no confirmó
- **THEN** `totp_enabled` permanece falso y el login sigue sin exigir segundo factor

### Requirement: Confirmación de enrolamiento activa el 2FA
El sistema SHALL exponer `POST /api/auth/2fa/confirm` que reciba el primer código TOTP. Si el código es válido para el secret enrolado, el sistema MUST setear `confirmed_at` y marcar `totp_enabled = true`. Si es inválido, el 2FA NO MUST activarse.

#### Scenario: Confirmación con código válido activa 2FA
- **WHEN** el usuario envía un código TOTP correcto para su secret enrolado
- **THEN** `confirmed_at` se setea, `totp_enabled` pasa a verdadero y el sistema responde 200

#### Scenario: Confirmación con código inválido no activa 2FA
- **WHEN** el usuario envía un código TOTP incorrecto
- **THEN** el sistema responde 400 y `totp_enabled` sigue falso

### Requirement: 2FA actúa como gate entre credenciales y emisión de sesión
El sistema SHALL, cuando un usuario con `totp_enabled = true` realiza login con credenciales válidas, NO emitir el par de tokens directamente. En su lugar MUST devolver un challenge de 2FA firmado de vida corta (~5 min, `type=2fa_challenge`). El par access+refresh SOLO MUST emitirse tras verificar el segundo factor.

#### Scenario: Login con 2FA habilitada devuelve challenge en vez de sesión
- **WHEN** un usuario con 2FA habilitada envía credenciales válidas
- **THEN** el sistema responde con un challenge de 2FA y NO emite access ni refresh token

#### Scenario: Verificación de segundo factor correcta emite sesión
- **WHEN** el usuario presenta el challenge y un código TOTP válido a `POST /api/auth/2fa/verify`
- **THEN** el sistema emite el par access + refresh

#### Scenario: Verificación de segundo factor incorrecta no emite sesión
- **WHEN** el usuario presenta el challenge y un código TOTP inválido
- **THEN** el sistema responde 401 y no emite ningún token

#### Scenario: Challenge vencido no emite sesión
- **WHEN** se presenta un challenge de 2FA cuyo `exp` ya pasó, aun con código válido
- **THEN** el sistema responde 401 y no emite tokens

### Requirement: Tolerancia de drift de reloj en TOTP
El sistema SHALL aceptar códigos TOTP dentro de una ventana de ±1 step (30 segundos) para tolerar el drift de reloj del dispositivo del usuario.

#### Scenario: Código del step anterior aún válido
- **WHEN** el usuario presenta un código generado en el step inmediatamente anterior (dentro de la ventana de 30s)
- **THEN** la verificación lo acepta como válido

## ADDED Requirements

### Requirement: Solicitud de recuperación genera token de un solo uso
El sistema SHALL exponer `POST /api/auth/forgot` que reciba un email. Si el email corresponde a un usuario activo, el sistema MUST generar un token aleatorio de alta entropía, persistir SOLO su hash en `password_reset_token` con `expires_at` corto (15 minutos) y `used_at = null`, y disparar el envío del token por email. El token en claro NUNCA MUST persistirse.

#### Scenario: Forgot para email existente genera token
- **WHEN** un usuario activo solicita recuperación con su email
- **THEN** el sistema persiste un `password_reset_token` con solo el hash, `expires_at` a 15 min y `used_at = null`, y dispara el envío

#### Scenario: Token de reset persistido como hash
- **WHEN** se inspecciona la fila de `password_reset_token`
- **THEN** la columna `token_hash` contiene un hash, no el token en claro

### Requirement: Respuesta uniforme que no revela existencia de cuenta
El sistema SHALL responder a `POST /api/auth/forgot` SIEMPRE con el mismo cuerpo y status (200), exista o no el email, para no filtrar qué cuentas están registradas.

#### Scenario: Forgot con email existente
- **WHEN** se solicita recuperación con un email registrado
- **THEN** el sistema responde 200 con un cuerpo uniforme

#### Scenario: Forgot con email inexistente
- **WHEN** se solicita recuperación con un email no registrado
- **THEN** el sistema responde 200 con el MISMO cuerpo uniforme y no persiste ningún token

### Requirement: Reset establece nueva password e invalida el token y las sesiones
El sistema SHALL exponer `POST /api/auth/reset` que reciba el token de reset y la nueva contraseña. El sistema MUST validar que el token exista, no esté usado y no esté vencido; setear la nueva password con Argon2id; marcar `used_at`; e invalidar (revocar) todas las sesiones activas del usuario. Un token inválido, usado o vencido MUST devolver 400. El schema MUST usar `extra='forbid'`.

#### Scenario: Reset con token válido
- **WHEN** se presenta un token de reset válido y una nueva password
- **THEN** la password del usuario se actualiza (nuevo hash Argon2id), el token queda con `used_at` seteado y las familias de refresh del usuario quedan revocadas

#### Scenario: Reuso de token de reset rechazado
- **WHEN** se presenta un token de reset que ya fue usado (`used_at` no nulo)
- **THEN** el sistema responde 400 y no cambia la password

#### Scenario: Token de reset vencido rechazado
- **WHEN** se presenta un token de reset cuyo `expires_at` ya pasó
- **THEN** el sistema responde 400 y no cambia la password

#### Scenario: Login con la nueva password tras reset
- **WHEN** el usuario hace login con la nueva password después de un reset exitoso
- **THEN** el login es exitoso, y la password anterior ya no es válida

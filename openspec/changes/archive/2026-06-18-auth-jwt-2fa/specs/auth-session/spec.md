## ADDED Requirements

### Requirement: Login con email y password emite par de tokens
El sistema SHALL exponer `POST /api/auth/login` que reciba email + password. El servicio MUST validar las credenciales contra el usuario del tenant correspondiente usando Argon2id. Si las credenciales son válidas y el usuario NO tiene 2FA habilitada, el sistema MUST emitir un par de tokens: un JWT access de 15 minutos y un refresh token con rotación. El schema de request MUST usar `extra='forbid'`.

#### Scenario: Login exitoso sin 2FA
- **WHEN** un usuario activo sin 2FA envía email y password correctos
- **THEN** el sistema responde 200 con un access token (JWT) y un refresh token

#### Scenario: Login con password incorrecta
- **WHEN** un usuario envía email correcto y password incorrecta
- **THEN** el sistema responde 401 con un mensaje uniforme y no emite ningún token

#### Scenario: Login con email inexistente
- **WHEN** se envía un email que no corresponde a ningún usuario del tenant
- **THEN** el sistema responde 401 con el mismo mensaje uniforme que en password incorrecta (no revela existencia de la cuenta)

#### Scenario: Schema rechaza campos no declarados
- **WHEN** el body de login incluye un campo no declarado
- **THEN** Pydantic rechaza la request con 422 (`extra='forbid'`)

### Requirement: Claims mínimos en el access token
El sistema SHALL emitir el access token como JWT firmado con `SECRET_KEY` conteniendo únicamente los claims mínimos: `sub` (user_id UUID), `tenant_id`, `roles` (lista de códigos vigentes), `exp`, `iat` y `type=access`. El token NO MUST contener permisos (se resuelven server-side). El `exp` MUST corresponder a 15 minutos.

#### Scenario: Access token contiene claims mínimos
- **WHEN** se decodifica un access token recién emitido
- **THEN** contiene `sub`, `tenant_id`, `roles`, `exp`, `iat` y `type=access`, y NO contiene permisos

#### Scenario: Expiración a 15 minutos
- **WHEN** se inspecciona el `exp` de un access token recién emitido
- **THEN** la diferencia entre `exp` e `iat` es de 15 minutos

### Requirement: get_current_user resuelve identidad solo desde el token verificado
El sistema SHALL proveer una dependency `get_current_user` que extraiga el Bearer token, verifique firma + `exp` + `type=access`, y resuelva `user_id`, `tenant_id` y `roles` EXCLUSIVAMENTE de los claims del token verificado. El usuario MUST cargarse vía repositorio tenant-scoped. Un token inválido, vencido o de un usuario inexistente/inactivo MUST devolver 401.

#### Scenario: Identidad resuelta desde token válido
- **WHEN** una petición llega con un access token válido
- **THEN** `get_current_user` devuelve la identidad (`user_id`, `tenant_id`, `roles`) tomada del token verificado

#### Scenario: Identidad inmutable por parámetro de la petición
- **WHEN** una petición incluye un `user_id` o `tenant_id` distinto en la URL, body o header al del token
- **THEN** `get_current_user` ignora esos parámetros y usa exclusivamente los claims del token verificado

#### Scenario: Token con firma inválida
- **WHEN** llega un token con firma manipulada
- **THEN** `get_current_user` responde 401

#### Scenario: Token vencido
- **WHEN** llega un access token cuyo `exp` ya pasó
- **THEN** `get_current_user` responde 401

#### Scenario: Token de usuario inexistente o inactivo
- **WHEN** el `sub` del token no corresponde a un usuario activo del `tenant_id` del token
- **THEN** `get_current_user` responde 401

### Requirement: Refresh con rotación single-use
El sistema SHALL exponer `POST /api/auth/refresh`. El refresh token MUST ser opaco y persistirse en DB solo como hash, con `family_id`, `expires_at` y `revoked_at`. Al refrescar con un token válido, el sistema MUST revocar (rotar) el token usado e emitir un par nuevo en la misma familia.

#### Scenario: Refresh válido rota y emite par nuevo
- **WHEN** se presenta un refresh token válido y no vencido
- **THEN** el sistema responde con un nuevo access + nuevo refresh, y el refresh anterior queda con `revoked_at` seteado

#### Scenario: Refresh vencido es rechazado
- **WHEN** se presenta un refresh token cuyo `expires_at` ya pasó
- **THEN** el sistema responde 401 y no emite tokens

### Requirement: Reuso de refresh token revoca la familia
El sistema SHALL detectar el reuso de un refresh token ya rotado. Si se presenta un refresh que pertenece a una familia conocida pero que ya fue revocado/consumido, el sistema MUST interpretarlo como robo, revocar la familia completa y rechazar la petición con 401.

#### Scenario: Reuso de un refresh ya rotado
- **WHEN** se presenta un refresh token que ya fue usado y rotado previamente
- **THEN** el sistema revoca todos los tokens de su familia y responde 401

#### Scenario: El par emitido tras el reuso queda invalidado
- **WHEN** un atacante rota un refresh robado y luego el dueño legítimo presenta su refresh (o viceversa)
- **THEN** al detectarse el reuso, ningún token de la familia sigue siendo válido para refrescar

### Requirement: Logout revoca la sesión
El sistema SHALL exponer `POST /api/auth/logout` que revoque el refresh token presentado y su familia, invalidando la capacidad de refrescar la sesión.

#### Scenario: Logout invalida el refresh
- **WHEN** un usuario autenticado hace logout con su refresh token
- **THEN** el refresh y su familia quedan revocados y un intento posterior de refresh con ese token responde 401

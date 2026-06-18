## MODIFIED Requirements

### Requirement: Claims mínimos en el access token
El sistema SHALL emitir el access token como JWT firmado con `SECRET_KEY` conteniendo únicamente los claims mínimos: `sub` (user_id UUID), `tenant_id`, `roles` (lista de códigos de los roles cuya asignación `UserRole` está **vigente** al momento de emitir), `exp`, `iat` y `type=access`. El claim `roles` es informativo (UX/diagnóstico) y NUNCA es fuente de autorización. El token NO MUST contener permisos: los permisos se resuelven server-side por request contra la base de datos. El `exp` MUST corresponder a 15 minutos.

#### Scenario: Access token contiene claims mínimos
- **WHEN** se decodifica un access token recién emitido
- **THEN** contiene `sub`, `tenant_id`, `roles`, `exp`, `iat` y `type=access`, y NO contiene permisos

#### Scenario: El claim roles solo incluye asignaciones vigentes
- **WHEN** un usuario tiene una asignación de rol vigente y otra vencida
- **THEN** el claim `roles` del token recién emitido incluye solo el código del rol vigente y omite el vencido

#### Scenario: Expiración a 15 minutos
- **WHEN** se inspecciona el `exp` de un access token recién emitido
- **THEN** la diferencia entre `exp` e `iat` es de 15 minutos

#### Scenario: Los permisos no viajan en el token
- **WHEN** se decodifica un access token
- **THEN** no contiene ningún permiso `modulo:accion`; la autorización se resuelve server-side

### Requirement: get_current_user resuelve identidad solo desde el token verificado
El sistema SHALL proveer una dependency `get_current_user` que extraiga el Bearer token, verifique firma + `exp` + `type=access`, y resuelva `user_id`, `tenant_id` y `roles` EXCLUSIVAMENTE de los claims del token verificado. El usuario MUST cargarse vía repositorio tenant-scoped. La autorización (permisos efectivos) NUNCA se deriva del claim `roles` del token; se resuelve server-side contra las asignaciones vigentes en DB. Un token inválido, vencido o de un usuario inexistente/inactivo MUST devolver 401.

#### Scenario: Identidad resuelta desde token válido
- **WHEN** una petición llega con un access token válido
- **THEN** `get_current_user` devuelve la identidad (`user_id`, `tenant_id`, `roles`) tomada del token verificado

#### Scenario: Identidad inmutable por parámetro de la petición
- **WHEN** una petición incluye un `user_id` o `tenant_id` distinto en la URL, body o header al del token
- **THEN** `get_current_user` ignora esos parámetros y usa exclusivamente los claims del token verificado

#### Scenario: La autorización no confía en el claim roles del token
- **WHEN** una petición presenta un token cuyo claim `roles` fue alterado para incluir roles no asignados en DB
- **THEN** los permisos efectivos se resuelven desde las asignaciones reales del usuario en DB y el claim `roles` manipulado no concede ninguna capacidad adicional

#### Scenario: Token con firma inválida
- **WHEN** llega un token con firma manipulada
- **THEN** `get_current_user` responde 401

#### Scenario: Token vencido
- **WHEN** llega un access token cuyo `exp` ya pasó
- **THEN** `get_current_user` responde 401

#### Scenario: Token de usuario inexistente o inactivo
- **WHEN** el `sub` del token no corresponde a un usuario activo del `tenant_id` del token
- **THEN** `get_current_user` responde 401

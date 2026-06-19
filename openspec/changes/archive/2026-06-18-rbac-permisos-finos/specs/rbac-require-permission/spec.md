## ADDED Requirements

### Requirement: Guard require_permission declara el permiso por endpoint
El sistema SHALL proveer una dependency factory `require_permission("modulo:accion")` que un endpoint declara para exigir un permiso concreto. La dependency MUST resolver la identidad desde `get_current_user` (JWT verificado), resolver los permisos efectivos server-side, y verificar que el `code` requerido esté presente. Si está, MUST conceder el acceso y entregar al Router un `PermissionGrant` con el `code` y el `scope` efectivo.

#### Scenario: Acceso concedido con permiso presente
- **WHEN** un usuario con `comunicacion:aprobar` en sus permisos efectivos llama a un endpoint que declara `require_permission("comunicacion:aprobar")`
- **THEN** la dependency concede el acceso y entrega un `PermissionGrant(code="comunicacion:aprobar", scope=<scope efectivo>)`

#### Scenario: Permiso requerido tomado del endpoint, identidad del token
- **WHEN** una petición llega con un `user_id` distinto en la URL al del token
- **THEN** la verificación de permiso usa exclusivamente la identidad del JWT verificado, ignorando el parámetro de la petición

### Requirement: Fail-closed devuelve 403 sin permiso explícito
El sistema SHALL denegar por defecto. Si el usuario autenticado NO posee el `code` requerido en sus permisos efectivos, la dependency MUST responder `403 Forbidden`. No existe flag de superusuario ni bypass: la ausencia de un permiso explícito MUST traducirse en 403.

#### Scenario: Usuario sin el permiso recibe 403
- **WHEN** un usuario autenticado SIN `comunicacion:aprobar` llama a un endpoint que lo exige
- **THEN** el sistema responde 403

#### Scenario: Usuario sin roles vigentes recibe 403
- **WHEN** un usuario cuyas asignaciones de rol están todas vencidas llama a cualquier endpoint protegido
- **THEN** el sistema responde 403

#### Scenario: Petición sin autenticación recibe 401 antes que 403
- **WHEN** una petición sin token válido llega a un endpoint protegido por `require_permission`
- **THEN** el sistema responde 401 (autenticación) antes de evaluar autorización

### Requirement: Semántica de scope propio versus global
El sistema SHALL exponer el `scope` (`global` o `propio`) del permiso concedido para que el Service aplique la verificación de pertenencia cuando corresponda. El guard `require_permission` MUST NOT verificar la pertenencia del recurso de negocio; SHALL proveer una utilidad `is_allowed(grant, owner_id, current_user_id)` que el Service usa: con `scope="global"` concede siempre; con `scope="propio"` concede solo si `owner_id == current_user_id`.

#### Scenario: Scope global concede sobre cualquier recurso
- **WHEN** un `PermissionGrant` con `scope="global"` se evalúa contra un recurso de otro usuario
- **THEN** `is_allowed` devuelve verdadero

#### Scenario: Scope propio concede solo sobre el recurso propio
- **WHEN** un `PermissionGrant` con `scope="propio"` se evalúa contra un recurso cuyo `owner_id` coincide con el usuario de la sesión
- **THEN** `is_allowed` devuelve verdadero

#### Scenario: Scope propio deniega sobre recurso ajeno
- **WHEN** un `PermissionGrant` con `scope="propio"` se evalúa contra un recurso cuyo `owner_id` NO coincide con el usuario de la sesión
- **THEN** `is_allowed` devuelve falso

#### Scenario: El guard no conoce el recurso de negocio
- **WHEN** un endpoint usa `require_permission` con un permiso `(propio)`
- **THEN** la concesión inicial depende solo de poseer el permiso, y la verificación de pertenencia queda delegada al Service vía `is_allowed`

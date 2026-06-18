## ADDED Requirements

### Requirement: Resolución de permisos efectivos por request
El sistema SHALL resolver los permisos efectivos de un usuario server-side, en cada request, como la **unión** de los permisos de todos sus roles. La resolución MUST ejecutarse contra la base de datos (nunca leerse del JWT) y MUST estar acotada por el `tenant_id` de la sesión. El resultado MUST ser un conjunto de `code` (`modulo:accion`) con su `scope` efectivo asociado.

#### Scenario: Unión de permisos de múltiples roles
- **WHEN** un usuario tiene los roles PROFESOR y COORDINADOR vigentes
- **THEN** sus permisos efectivos son la unión de los permisos de ambos roles

#### Scenario: Permisos resueltos desde DB, no desde el token
- **WHEN** se manipula la lista `roles` dentro del JWT para incluir un rol que el usuario no tiene asignado en DB
- **THEN** los permisos efectivos resueltos NO incluyen los del rol manipulado (la resolución ignora los `roles` del token y consulta las asignaciones reales)

#### Scenario: Permisos acotados por tenant
- **WHEN** se resuelven los permisos efectivos de un usuario
- **THEN** solo se consideran roles y filas de matriz del `tenant_id` de la sesión

### Requirement: Vigencia temporal acota los permisos efectivos
El sistema SHALL considerar únicamente las asignaciones `UserRole` **vigentes** al resolver permisos efectivos. Una asignación está vigente si `desde ≤ now` y (`hasta IS NULL` o `now < hasta`) y no está soft-deleteada. Una asignación vencida o aún no iniciada MUST NO otorgar ningún permiso, pero MUST conservarse en el histórico.

#### Scenario: Asignación vigente otorga permisos
- **WHEN** un usuario tiene una asignación de rol con `desde` en el pasado y `hasta` NULL
- **THEN** sus permisos efectivos incluyen los del rol asignado

#### Scenario: Asignación vencida no otorga permisos
- **WHEN** un usuario tiene una asignación de rol cuyo `hasta` ya pasó
- **THEN** sus permisos efectivos NO incluyen los de ese rol, y la asignación permanece registrada en el histórico

#### Scenario: Asignación futura no otorga permisos
- **WHEN** un usuario tiene una asignación de rol cuyo `desde` es futuro
- **THEN** sus permisos efectivos NO incluyen los de ese rol todavía

### Requirement: Resolución del scope efectivo ante conflicto
El sistema SHALL resolver un scope efectivo por permiso cuando el mismo `code` llega por más de un rol. Si un rol concede el permiso con `scope="global"` y otro con `scope="propio"`, el scope efectivo MUST ser `global` (el más permisivo gana).

#### Scenario: Global prevalece sobre propio
- **WHEN** un usuario obtiene `calificaciones:importar` por un rol con `scope="propio"` y por otro con `scope="global"`
- **THEN** su scope efectivo para `calificaciones:importar` es `global`

#### Scenario: Solo propio cuando ningún rol lo concede global
- **WHEN** un usuario obtiene `calificaciones:importar` únicamente por roles con `scope="propio"`
- **THEN** su scope efectivo para `calificaciones:importar` es `propio`

### Requirement: Usuario sin roles vigentes no tiene permisos
El sistema SHALL devolver un conjunto vacío de permisos efectivos para un usuario sin roles vigentes. La ausencia de permisos MUST traducirse en denegación (fail-closed) en cualquier endpoint protegido.

#### Scenario: Conjunto vacío sin roles vigentes
- **WHEN** se resuelven los permisos efectivos de un usuario sin ninguna asignación vigente
- **THEN** el conjunto de permisos efectivos es vacío

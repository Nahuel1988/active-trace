## MODIFIED Requirements

### Requirement: Resolución de permisos efectivos por request
El sistema SHALL resolver los permisos efectivos de un usuario server-side, en cada request, como la **unión** de los permisos de todos sus roles efectivos. Los roles efectivos MUST obtenerse de DOS fuentes complementarias: (a) la tabla `user_role` (vínculo global usuario↔rol del tenant, para roles sin contexto académico como ADMIN o FINANZAS) y (b) la tabla `asignacion` (vínculo usuario↔rol con contexto académico, para roles operativos como PROFESOR, TUTOR, COORDINADOR o NEXO). La resolución MUST ejecutarse contra la base de datos (nunca leerse del JWT) y MUST estar acotada por el `tenant_id` de la sesión. El resultado MUST ser un conjunto de `code` (`modulo:accion`) con su `scope` efectivo asociado. El scoping académico (acotar el permiso a una materia/carrera/cohorte específica) NO MUST ser inferido por `require_permission`: corresponde al endpoint y al repository filtrar por el contexto cuando aplique.

#### Scenario: Unión de permisos de múltiples roles
- **WHEN** un usuario tiene los roles PROFESOR y COORDINADOR vigentes
- **THEN** sus permisos efectivos son la unión de los permisos de ambos roles

#### Scenario: Unión de UserRole y Asignacion
- **WHEN** un usuario tiene ADMIN en `user_role` y PROFESOR en `asignacion` (ambos vigentes en el mismo tenant)
- **THEN** sus permisos efectivos son la unión de los permisos de ambos roles

#### Scenario: Sólo UserRole sin Asignacion
- **WHEN** un usuario ADMIN no tiene asignaciones académicas
- **THEN** sus permisos efectivos provienen únicamente de `user_role` y NO se rompe la resolución

#### Scenario: Sólo Asignacion sin UserRole
- **WHEN** un usuario PROFESOR no tiene entradas en `user_role` pero sí en `asignacion`
- **THEN** sus permisos efectivos provienen únicamente de `asignacion` y NO se rompe la resolución

#### Scenario: Permisos resueltos desde DB, no desde el token
- **WHEN** se manipula la lista `roles` dentro del JWT para incluir un rol que el usuario no tiene asignado en DB
- **THEN** los permisos efectivos resueltos NO incluyen los del rol manipulado (la resolución ignora los `roles` del token y consulta las asignaciones reales)

#### Scenario: Permisos acotados por tenant
- **WHEN** se resuelven los permisos efectivos de un usuario
- **THEN** solo se consideran roles y filas de matriz del `tenant_id` de la sesión

### Requirement: Vigencia temporal acota los permisos efectivos
El sistema SHALL considerar únicamente las asignaciones **vigentes** al resolver permisos efectivos, en AMBAS fuentes: `user_role` y `asignacion`. Una asignación está vigente si `desde ≤ now` y (`hasta IS NULL` o `now < hasta`) y no está soft-deleteada. Una asignación vencida, soft-deleted o aún no iniciada MUST NO otorgar ningún permiso, pero MUST conservarse en el histórico.

#### Scenario: UserRole vigente otorga permisos
- **WHEN** un usuario tiene una entrada en `user_role` con `desde` en el pasado y `hasta` NULL
- **THEN** sus permisos efectivos incluyen los del rol asignado

#### Scenario: Asignacion vigente otorga permisos
- **WHEN** un usuario tiene una entrada en `asignacion` con `desde` en el pasado y `hasta` NULL
- **THEN** sus permisos efectivos incluyen los del rol asignado

#### Scenario: Asignacion vencida no otorga permisos
- **WHEN** un usuario tiene una entrada en `asignacion` cuyo `hasta` ya pasó
- **THEN** sus permisos efectivos NO incluyen los de ese rol, y la asignación permanece registrada en el histórico

#### Scenario: Asignacion soft-deleted no otorga permisos
- **WHEN** un usuario tiene una entrada en `asignacion` con `deleted_at` no nulo
- **THEN** sus permisos efectivos NO incluyen los de ese rol

#### Scenario: Asignacion futura no otorga permisos
- **WHEN** un usuario tiene una entrada en `asignacion` cuyo `desde` es futuro
- **THEN** sus permisos efectivos NO incluyen los de ese rol todavía

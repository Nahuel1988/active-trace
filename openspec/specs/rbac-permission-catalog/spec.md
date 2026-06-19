## ADDED Requirements

### Requirement: Modelo de permiso con clave modulo:accion
El sistema SHALL definir un modelo `Permiso` tenant-scoped que represente una capacidad atómica expresada como `modulo:accion`. Cada permiso MUST tener `modulo`, `accion` y una clave derivada `code = "{modulo}:{accion}"`. El `code` MUST ser único por tenant (`UNIQUE(tenant_id, code)`) y MUST validarse contra el formato `^[a-z_]+:[a-z_]+$`. El modelo MUST aplicar soft delete (`deleted_at`) y nunca borrarse físicamente.

#### Scenario: Permiso válido se crea con code derivado
- **WHEN** se crea un permiso con `modulo="comunicacion"` y `accion="aprobar"`
- **THEN** su `code` resultante es `comunicacion:aprobar`

#### Scenario: Code duplicado en el mismo tenant es rechazado
- **WHEN** se intenta crear un segundo permiso con el mismo `code` en el mismo tenant
- **THEN** el sistema rechaza la operación por violación de unicidad `(tenant_id, code)`

#### Scenario: Mismo code permitido en tenants distintos
- **WHEN** dos tenants distintos crean cada uno un permiso `calificaciones:importar`
- **THEN** ambos coexisten sin conflicto

#### Scenario: Formato de code inválido es rechazado
- **WHEN** se intenta crear un permiso cuyo `code` no cumple `^[a-z_]+:[a-z_]+$` (ej. `Comunicacion:Aprobar` o `comunicacion`)
- **THEN** el sistema rechaza la creación con error de validación

### Requirement: Matriz rol por permiso como datos administrables
El sistema SHALL definir un modelo de asociación `RolPermiso` tenant-scoped con PK compuesta `(tenant_id, role_id, permiso_id)` que vincule un rol con un permiso. Cada fila MUST llevar un `scope` ∈ {`global`, `propio`} que codifique el alcance de la capacidad para ese rol. La matriz MUST ser administrable como datos (filas en base de datos), NUNCA hardcodeada en el código.

#### Scenario: Asignar un permiso a un rol con scope global
- **WHEN** se asigna el permiso `comunicacion:enviar` al rol COORDINADOR con `scope="global"`
- **THEN** existe una fila `RolPermiso(role_id=COORDINADOR, permiso_id=comunicacion:enviar, scope="global")` en ese tenant

#### Scenario: Asignar un permiso a un rol con scope propio
- **WHEN** se asigna el permiso `comunicacion:enviar` al rol PROFESOR con `scope="propio"`
- **THEN** existe una fila `RolPermiso(role_id=PROFESOR, permiso_id=comunicacion:enviar, scope="propio")` en ese tenant

#### Scenario: Quitar un permiso de un rol
- **WHEN** un administrador elimina la asociación rol↔permiso
- **THEN** la fila correspondiente deja de existir y el rol pierde esa capacidad efectiva

#### Scenario: Matriz acotada por tenant
- **WHEN** se consulta la matriz de un tenant
- **THEN** solo se devuelven las filas `RolPermiso` de ese tenant, nunca de otro

### Requirement: Seed de la matriz base del dominio
El sistema SHALL sembrar, vía migración, el catálogo de permisos y la matriz base de capacidades de `03_actores_y_roles.md §3.3` para los roles del dominio (ALUMNO, TUTOR, PROFESOR, COORDINADOR, NEXO, ADMIN, FINANZAS). El seed MUST aplicarse por tenant existente y MUST ser idempotente (re-ejecutable sin duplicar filas). Las celdas marcadas `(propio)` en la matriz MUST sembrarse con `scope="propio"`; las marcadas `✅` con `scope="global"`; las marcadas `—` MUST NO generar fila.

#### Scenario: Permiso global de la matriz queda sembrado
- **WHEN** se aplica el seed sobre un tenant
- **THEN** el rol COORDINADOR tiene `comunicacion:aprobar` con `scope="global"` (celda ✅ de la matriz)

#### Scenario: Permiso propio de la matriz queda sembrado con scope propio
- **WHEN** se aplica el seed sobre un tenant
- **THEN** el rol PROFESOR tiene `calificaciones:importar` con `scope="propio"` (celda `(propio)` de la matriz)

#### Scenario: Celda vacía no genera permiso
- **WHEN** se aplica el seed sobre un tenant
- **THEN** el rol ALUMNO NO tiene `liquidaciones:cerrar` (celda — de la matriz)

#### Scenario: Seed idempotente
- **WHEN** el seed se ejecuta dos veces sobre el mismo tenant
- **THEN** no se duplican filas de catálogo ni de matriz

### Requirement: Administración del catálogo y la matriz
El sistema SHALL exponer endpoints para administrar roles, permisos y la matriz rol↔permiso de un tenant. Todos estos endpoints MUST exigir el permiso `usuarios:gestionar` y resolverse fail-closed (sin el permiso → 403). Los schemas de request MUST usar `extra='forbid'`. Las operaciones MUST estar acotadas por el `tenant_id` de la sesión.

#### Scenario: Admin lista la matriz de su tenant
- **WHEN** un usuario con `usuarios:gestionar` consulta la matriz rol↔permiso
- **THEN** el sistema responde 200 con las filas de su tenant

#### Scenario: Usuario sin permiso no puede administrar el catálogo
- **WHEN** un usuario sin `usuarios:gestionar` intenta crear o modificar un permiso
- **THEN** el sistema responde 403

#### Scenario: Administración acotada por tenant
- **WHEN** un admin intenta operar sobre un permiso o rol de otro tenant
- **THEN** el sistema lo trata como inexistente (404) y nunca permite cruzar tenants

#### Scenario: Schema rechaza campos no declarados
- **WHEN** el body de creación de un permiso incluye un campo no declarado
- **THEN** Pydantic rechaza la request con 422 (`extra='forbid'`)

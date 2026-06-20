## ADDED Requirements

### Requirement: Modelo versionado de padrón por (materia, cohorte)

El sistema SHALL mantener un historial versionado de padrones por combinación `(tenant_id, materia_id, cohorte_id)`. Cada carga genera una nueva `VersionPadron`. Solo puede haber una versión activa por esa tupla en simultáneo. Al activar una nueva versión, la anterior se desactiva (no se borra). Las entradas (`EntradaPadron`) pertenecen a una versión y no se modifican retroactivamente.

#### Scenario: Activar nueva versión desactiva la anterior

- **WHEN** se activa una nueva `VersionPadron` para `(materia_id=M, cohorte_id=C, tenant_id=T)`
- **THEN** la versión previamente activa para esa misma tupla pasa a `activa = false`
- **AND** la nueva versión queda con `activa = true`
- **AND** el historial de versiones anteriores se conserva en DB

#### Scenario: No puede haber dos versiones activas simultáneas

- **WHEN** existe una versión activa para `(materia_id=M, cohorte_id=C, tenant_id=T)`
- **AND** se intenta activar una segunda versión para la misma tupla sin desactivar la primera
- **THEN** el sistema rechaza la operación con error de invariante violada

#### Scenario: Primera versión activa cuando no hay versión previa

- **WHEN** no existe ninguna `VersionPadron` para `(materia_id=M, cohorte_id=C, tenant_id=T)`
- **AND** se activa una nueva versión
- **THEN** esa versión queda con `activa = true` sin necesidad de desactivar ninguna anterior

### Requirement: EntradaPadron con email cifrado y usuario_id nullable

Cada `EntradaPadron` pertenece a una `VersionPadron` y SHALL contener los campos de identidad del alumno. El campo `email` es PII y SHALL almacenarse cifrado en reposo con AES-256. El campo `usuario_id` es nullable: un alumno puede estar en el padrón antes de tener cuenta en el sistema.

#### Scenario: Entrada con alumno sin cuenta

- **WHEN** se carga una `EntradaPadron` con `email` válido y sin `usuario_id`
- **THEN** el sistema acepta la entrada con `usuario_id = null`
- **AND** el `email` se almacena cifrado en la base de datos

#### Scenario: Entrada con alumno que ya tiene cuenta

- **WHEN** se carga una `EntradaPadron` con `usuario_id` apuntando a un `Usuario` existente del mismo tenant
- **THEN** el sistema almacena la entrada con el vínculo al usuario
- **AND** el `email` se almacena cifrado igualmente

#### Scenario: Email de EntradaPadron nunca aparece en texto plano en logs

- **WHEN** se produce cualquier operación sobre `EntradaPadron`
- **THEN** el valor del campo `email` NO aparece en texto plano en los logs del sistema
- **AND** solo se expone desencriptado en respuestas de API autorizadas

### Requirement: Aislamiento multi-tenant del padrón

Toda operación sobre `VersionPadron` y `EntradaPadron` SHALL estar scoped al `tenant_id` derivado del JWT del usuario autenticado. No existe ninguna ruta de acceso a padrones de otro tenant.

#### Scenario: Consulta de padrón scoped al tenant del JWT

- **WHEN** un usuario autenticado consulta el padrón de una materia
- **THEN** el sistema devuelve solo las versiones y entradas cuyo `tenant_id` coincide con el del JWT
- **AND** no devuelve ningún dato de otros tenants aunque existan en DB

#### Scenario: Intento de acceso a materia de otro tenant

- **WHEN** se solicita el padrón de una `materia_id` que pertenece a un tenant distinto al del JWT
- **THEN** el sistema responde `404 Not Found` (no revela que la materia existe en otro tenant)

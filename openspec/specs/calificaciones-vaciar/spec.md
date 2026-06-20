## ADDED Requirements

### Requirement: Vaciar calificaciones de una materia (F1.5, RN-04)

El sistema SHALL permitir que un docente elimine (soft-delete) todas sus calificaciones importadas para una materia. La operación SHALL afectar solo las calificaciones donde `creado_por = usuario_id` del JWT. NO SHALL afectar calificaciones de otros docentes de la misma materia. SHALL auditar la operación.

#### Scenario: Vaciar calificaciones propias

- **WHEN** un docente ejecuta vaciar para materia M
- **AND** tiene 30 calificaciones con `creado_por = su_id` para materia M
- **THEN** las 30 calificaciones se marcan con `deleted_at = now()` y `deleted_by = su_id`
- **AND** las calificaciones de otros docentes para materia M permanecen intactas

#### Scenario: Vaciar sin calificaciones propias

- **WHEN** un docente ejecuta vaciar para materia M
- **AND** no tiene calificaciones con `creado_por = su_id` para materia M
- **THEN** la operación es exitosa (204) sin afectar ningún registro

#### Scenario: Vaciar no afecta otras materias

- **WHEN** un docente ejecuta vaciar para materia M
- **THEN** las calificaciones del mismo docente para materia N permanecen intactas

### Requirement: Aislamiento multi-tenant en vaciado

La operación de vaciado SHALL estar scoped al tenant del JWT. No SHALL poder vaciar calificaciones de otro tenant.

#### Scenario: Vaciar en materia de otro tenant

- **WHEN** un usuario intenta vaciar calificaciones de una materia que pertenece a otro tenant
- **THEN** el sistema responde `404 Not Found`

### Requirement: Soft-delete preserva auditoría

El vaciado SHALL ser soft-delete. Los registros SHALL permanecer en DB con `deleted_at` y `deleted_by` seteados. No se permite hard-delete sobre calificaciones.

#### Scenario: Calificaciones vaciadas son recuperables desde DB

- **WHEN** se ejecuta vaciado sobre calificaciones
- **THEN** los registros permanecen en la tabla `calificacion` con `deleted_at` no nulo
- **AND** una consulta directa a DB (con acceso) puede ver los registros eliminados

### Requirement: Auditoría de vaciado

Cada operación de vaciado SHALL generar un registro de auditoría con código `CALIFICACIONES_IMPORTAR` y la cantidad de calificaciones afectadas.

#### Scenario: Auditoría al vaciar calificaciones

- **WHEN** se ejecuta vaciado que afecta 15 calificaciones
- **THEN** se crea un `AuditLog` con `accion = "CALIFICACIONES_IMPORTAR"`, `filas_afectadas = 15`, `materia_id = materia_id`

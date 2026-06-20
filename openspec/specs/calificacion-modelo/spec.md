## ADDED Requirements

### Requirement: Modelo Calificacion con FK a EntradaPadron

El sistema SHALL mantener un modelo `Calificacion` que registre la nota o estado de un estudiante en una actividad evaluable de una materia. SHALL tener FK a `EntradaPadron` (C-09) y a `Materia`. SHALL soportar `nota_numerica` (decimal, nullable) y `nota_textual` (texto, nullable), con al menos uno de los dos no nulo. SHALL tener `origen` de tipo enum (Importado | Manual). SHALL tener `creado_por` FK a Usuario para permitir aislamiento por docente (RN-04).

#### Scenario: Calificacion con nota numérica

- **WHEN** se crea una `Calificacion` con `nota_numerica = 8.5` y sin `nota_textual`
- **THEN** el sistema almacena la calificación
- **AND** `nota_numerica = 8.5`
- **AND** `nota_textual` es nulo

#### Scenario: Calificacion con nota textual

- **WHEN** se crea una `Calificacion` con `nota_textual = "Satisfactorio"` y sin `nota_numerica`
- **THEN** el sistema almacena la calificación
- **AND** `nota_textual = "Satisfactorio"`
- **AND** `nota_numerica` es nulo

#### Scenario: Calificacion rechaza ambos campos nulos

- **WHEN** se intenta crear una `Calificacion` con `nota_numerica = null` y `nota_textual = null`
- **THEN** el sistema rechaza la operación con error de validación

#### Scenario: Calificacion con origen Importado

- **WHEN** se importa una calificación desde archivo del LMS
- **THEN** `origen` se setea a `Importado`

#### Scenario: Calificacion con origen Manual

- **WHEN** se crea una calificación manualmente (fuera del flujo de importación)
- **THEN** `origen` se setea a `Manual`

### Requirement: FK creado_por resuelve identidad desde JWT

`Calificacion.creado_por` SHALL setearse automáticamente desde la identidad del usuario autenticado (JWT). El sistema SHALL NEVER aceptar `creado_por` desde datos de la petición (regla de seguridad: identidad siempre desde la sesión).

#### Scenario: creado_por se asigna desde el JWT al importar

- **WHEN** un usuario autenticado importa calificaciones
- **THEN** todas las calificaciones creadas tienen `creado_por = usuario_id` del JWT
- **AND** ningún campo del body de la petición puede modificar `creado_por`

### Requirement: Soft-delete en Calificacion

Calificacion SHALL soportar soft-delete. Al eliminar, se setea `deleted_at = now()` y `deleted_by = usuario_id`. Nunca se ejecuta hard-delete.

#### Scenario: Soft delete de calificaciones

- **WHEN** se ejecuta vaciado de calificaciones para `(usuario_id, materia_id)`
- **THEN** las calificaciones del usuario para esa materia quedan con `deleted_at` y `deleted_by` seteados
- **AND** los registros permanecen en la base de datos

### Requirement: Aislamiento multi-tenant de Calificacion

Toda operación sobre `Calificacion` SHALL estar scoped al `tenant_id` derivado del JWT. No existe ninguna ruta de acceso a calificaciones de otro tenant.

#### Scenario: Consulta de calificaciones scoped al tenant

- **WHEN** un usuario autenticado consulta calificaciones de una materia
- **THEN** el sistema devuelve solo las calificaciones cuyo `tenant_id` coincide con el del JWT
- **AND** no devuelve ningún dato de otros tenants aunque existan en DB

#### Scenario: Intento de acceso a calificaciones de otro tenant

- **WHEN** se solicitan calificaciones de una `materia_id` que pertenece a un tenant distinto al del JWT
- **THEN** el sistema responde `404 Not Found`

### Requirement: Índices compuestos para performance de consultas

Calificacion SHALL tener índices compuestos para consultas frecuentes: `(tenant_id, materia_id, creado_por)` para filtro por docente y materia, y `(tenant_id, entrada_padron_id)` para cruce con padrón.

#### Scenario: Índices creados en migración

- **WHEN** se ejecuta la migración 009
- **THEN** se crean los índices compuestos sobre `(tenant_id, materia_id, creado_por)` y `(tenant_id, entrada_padron_id)` en la tabla `calificacion`

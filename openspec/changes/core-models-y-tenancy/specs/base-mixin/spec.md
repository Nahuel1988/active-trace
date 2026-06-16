## ADDED Requirements

### Requirement: Mixin base aplica UUID, tenant_id, timestamps y soft delete
El sistema SHALL proveer un mixin `TenantScopedMixin` que todo modelo de dominio puede heredar. El mixin agrega: `id` (UUID v4, PK, generado en Python), `tenant_id` (UUID, FK → tenant.id, NOT NULL, indexado), `created_at` (datetime UTC, auto-set en INSERT), `updated_at` (datetime UTC, auto-set en INSERT y UPDATE), `deleted_at` (datetime UTC nullable, NULL = activo).

#### Scenario: UUID generado en Python antes de insertar
- **WHEN** se instancia un modelo que usa `TenantScopedMixin` sin proveer `id` explícito
- **THEN** el campo `id` tiene un UUID v4 válido antes de llegar a la base de datos

#### Scenario: Timestamps auto-gestionados en INSERT
- **WHEN** se persiste un modelo nuevo
- **THEN** `created_at` y `updated_at` contienen el timestamp UTC del momento de inserción

#### Scenario: `updated_at` se actualiza en UPDATE
- **WHEN** se modifica un campo de un modelo existente y se persiste
- **THEN** `updated_at` refleja el timestamp UTC de la actualización

### Requirement: Soft delete via `deleted_at`
El sistema SHALL implementar eliminación lógica en todos los modelos que usan `TenantScopedMixin`. Eliminar un registro significa setear `deleted_at` al timestamp UTC actual, nunca ejecutar `DELETE` físico.

#### Scenario: Registro marcado como eliminado
- **WHEN** se ejecuta soft delete sobre un registro
- **THEN** `deleted_at` pasa a tener un timestamp UTC y el registro sigue en la tabla

#### Scenario: Registro eliminado no aparece en listados por defecto
- **WHEN** el repositorio base lista registros de un modelo
- **THEN** los registros con `deleted_at IS NOT NULL` no aparecen en el resultado

#### Scenario: Hard delete bloqueado a nivel aplicación
- **WHEN** se llama a un método del repositorio base
- **THEN** ningún método del `BaseRepository` ejecuta `DELETE` físico

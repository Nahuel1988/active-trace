## ADDED Requirements

### Requirement: BaseRepository aplica scope de tenant en todas las queries
El sistema SHALL proveer un `BaseRepository[T]` genérico parametrizado por modelo. Todo método que lee datos (`get`, `list`, `exists`) MUST filtrar por `tenant_id` de forma explícita y obligatoria. No existe un método de lectura sin scope de tenant en esta clase base.

#### Scenario: `get` devuelve registro del tenant correcto
- **WHEN** se llama a `repo.get(id=x, tenant_id=t1)` y el registro existe para el tenant `t1`
- **THEN** retorna el registro correspondiente

#### Scenario: `get` no devuelve registros de otro tenant
- **WHEN** se llama a `repo.get(id=x, tenant_id=t1)` y el registro `x` pertenece al tenant `t2`
- **THEN** retorna `None`

#### Scenario: `list` devuelve solo registros del tenant
- **WHEN** existen registros de tenant `t1` y `t2`, y se llama a `repo.list(tenant_id=t1)`
- **THEN** el resultado contiene solo registros de `t1`

### Requirement: Aislamiento multi-tenant garantizado
El sistema SHALL garantizar que un usuario autenticado en el tenant A nunca pueda leer ni modificar datos del tenant B a través del `BaseRepository`.

#### Scenario: Aislamiento en lectura
- **WHEN** se crean registros en tenant A y tenant B, y se listan con `tenant_id=A`
- **THEN** el resultado solo contiene registros del tenant A, con conteo exacto esperado

#### Scenario: Aislamiento en soft delete
- **WHEN** se ejecuta soft delete con `tenant_id=A` sobre un ID que pertenece al tenant B
- **THEN** la operación no afecta ningún registro (0 filas modificadas)

### Requirement: Soft delete integrado en el repositorio base
El sistema SHALL incluir en `BaseRepository` un método `soft_delete(id, tenant_id)` que setea `deleted_at` al timestamp UTC actual. Los métodos `get` y `list` MUST excluir registros con `deleted_at IS NOT NULL` por defecto.

#### Scenario: Registro eliminado no aparece en `list`
- **WHEN** un registro es soft-deleted y luego se llama a `list(tenant_id=...)`
- **THEN** el registro no aparece en el resultado

#### Scenario: `get` no retorna registro soft-deleted
- **WHEN** un registro es soft-deleted y se llama a `get(id=..., tenant_id=...)`
- **THEN** retorna `None`

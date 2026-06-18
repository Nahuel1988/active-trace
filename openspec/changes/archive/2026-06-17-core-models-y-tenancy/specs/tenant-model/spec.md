## ADDED Requirements

### Requirement: Entidad Tenant persiste en PostgreSQL
El sistema SHALL contar con una tabla `tenant` en PostgreSQL que almacene la información de cada institución. Cada tenant tiene: `id` (UUID PK), `slug` (texto único, identificador legible por máquina), `nombre` (texto), `activo` (booleano, default `true`), `created_at` y `updated_at` (timestamps auto-gestionados).

#### Scenario: Creación de tenant nuevo
- **WHEN** se inserta un registro en la tabla `tenant` con slug y nombre válidos
- **THEN** el registro queda persistido con un UUID único, `activo = true`, y timestamps `created_at` y `updated_at` con el momento de inserción

#### Scenario: Slug único por institución
- **WHEN** se intenta insertar un segundo tenant con el mismo `slug`
- **THEN** la base de datos rechaza la inserción con error de constraint de unicidad

#### Scenario: Migración 001 crea la tabla
- **WHEN** se ejecuta `alembic upgrade head` en una base de datos vacía
- **THEN** la tabla `tenant` existe con todas sus columnas y constraints

### Requirement: Tenant como raíz del modelo de datos
El sistema SHALL garantizar que `tenant_id` esté presente en toda tabla de dominio futura como FK no nula hacia `tenant.id`, estableciendo al `Tenant` como raíz del árbol de datos.

#### Scenario: Referencia íntegra
- **WHEN** se inserta cualquier entidad de dominio con un `tenant_id` inexistente
- **THEN** la base de datos rechaza la inserción por violación de FK

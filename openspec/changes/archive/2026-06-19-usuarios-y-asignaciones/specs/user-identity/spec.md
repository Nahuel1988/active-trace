## MODIFIED Requirements

### Requirement: Modelo User con identidad por UUID interno
El sistema SHALL proveer un modelo `User` que herede `BaseMixin` (UUID `id`, `tenant_id`, `created_at`, `updated_at`, `deleted_at`). El `id` UUID interno MUST ser el único selector válido de identidad. El `User` MUST tener `tenant_id` FK no nula hacia `tenant.id`. La migración `002` MUST crear la tabla `user`. La migración `006` MUST extender la tabla `user` con las columnas adicionales `nombre`, `apellidos`, `dni_encrypted`, `cuil_encrypted`, `cbu_encrypted`, `alias_cbu_encrypted`, `banco`, `regional`, `legajo_profesional` y `facturador` (booleano NOT NULL DEFAULT false). Las nuevas columnas de atributos institucionales MUST ser NULLABLE para permitir la convivencia con usuarios pre-existentes creados por C-02.

#### Scenario: Creación de usuario con UUID
- **WHEN** se crea un usuario con email, password y tenant válidos
- **THEN** el registro queda persistido con un UUID `id` único, su `tenant_id`, `is_active = true` y timestamps automáticos

#### Scenario: Usuario pertenece a un tenant
- **WHEN** se intenta crear un usuario con un `tenant_id` inexistente
- **THEN** la base de datos rechaza la inserción por violación de FK

#### Scenario: Migración 002 crea la tabla user
- **WHEN** se ejecuta `alembic upgrade head` partiendo de la migración 001
- **THEN** la tabla `user` existe con todas sus columnas y constraints

#### Scenario: Migración 006 agrega columnas PII y atributos institucionales
- **WHEN** se ejecuta `alembic upgrade 006` partiendo de la migración 005
- **THEN** la tabla `user` tiene las columnas `nombre`, `apellidos`, `dni_encrypted`, `cuil_encrypted`, `cbu_encrypted`, `alias_cbu_encrypted`, `banco`, `regional`, `legajo_profesional` y `facturador` con sus tipos y nullabilities declarados

#### Scenario: Usuario pre-existente sigue funcionando tras la migración 006
- **WHEN** un usuario creado por C-02 (sin PII institucional) es consultado tras `alembic upgrade 006`
- **THEN** el registro se lee correctamente con las nuevas columnas en NULL (o `facturador = false`) y los flujos de auth no se rompen

### Requirement: Legajo es atributo de negocio, nunca credencial
El sistema SHALL tratar el `legajo` y el `legajo_profesional` (cuando existan) como atributos de negocio nullable. Ninguno MUST usarse como clave primaria, credencial de autenticación ni selector de identidad o de sesión. La unicidad NO MUST imponerse sobre estos campos en esta capacidad.

#### Scenario: Usuario sin legajo es válido
- **WHEN** se crea un usuario sin legajo
- **THEN** el registro se persiste correctamente con `legajo = null`

#### Scenario: Usuario sin legajo profesional es válido
- **WHEN** se crea un usuario sin `legajo_profesional`
- **THEN** el registro se persiste correctamente con `legajo_profesional = null`

#### Scenario: Legajo no autentica
- **WHEN** se intenta autenticar usando el legajo como credencial o selector
- **THEN** el flujo de autenticación lo ignora — solo el UUID interno y las credenciales verificadas determinan la identidad

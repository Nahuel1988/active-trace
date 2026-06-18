## ADDED Requirements

### Requirement: Modelo User con identidad por UUID interno
El sistema SHALL proveer un modelo `User` que herede `BaseMixin` (UUID `id`, `tenant_id`, `created_at`, `updated_at`, `deleted_at`). El `id` UUID interno MUST ser el único selector válido de identidad. El `User` MUST tener `tenant_id` FK no nula hacia `tenant.id`. La migración `002` MUST crear la tabla `user`.

#### Scenario: Creación de usuario con UUID
- **WHEN** se crea un usuario con email, password y tenant válidos
- **THEN** el registro queda persistido con un UUID `id` único, su `tenant_id`, `is_active = true` y timestamps automáticos

#### Scenario: Usuario pertenece a un tenant
- **WHEN** se intenta crear un usuario con un `tenant_id` inexistente
- **THEN** la base de datos rechaza la inserción por violación de FK

#### Scenario: Migración 002 crea la tabla user
- **WHEN** se ejecuta `alembic upgrade head` partiendo de la migración 001
- **THEN** la tabla `user` existe con todas sus columnas y constraints

### Requirement: Email PII cifrado con lookup determinístico
El sistema SHALL almacenar el email como PII cifrada AES-256 en `email_encrypted` (vía `EncryptionService`) y NUNCA en texto plano en la base de datos. Para login y unicidad, el sistema MUST mantener una columna `email_lookup` con un hash determinístico (HMAC-SHA256) del email normalizado, con constraint `UNIQUE(tenant_id, email_lookup)`.

#### Scenario: Email cifrado en DB
- **WHEN** se persiste un usuario con email `docente@ejemplo.com`
- **THEN** la columna `email_encrypted` contiene ciphertext base64 y NO el email en claro

#### Scenario: Búsqueda por email sin descifrar
- **WHEN** se busca al usuario por su email durante el login
- **THEN** la búsqueda usa `email_lookup` (hash determinístico) y encuentra el registro sin descifrar la columna cifrada

#### Scenario: Email único por tenant
- **WHEN** se intenta crear un segundo usuario con el mismo email en el mismo tenant
- **THEN** la base de datos rechaza la inserción por violación de unicidad `(tenant_id, email_lookup)`

#### Scenario: Mismo email permitido en tenants distintos
- **WHEN** dos tenants distintos tienen un usuario con el mismo email
- **THEN** ambos registros coexisten sin violar la unicidad (el scope es por tenant)

### Requirement: Password almacenado con Argon2id
El sistema SHALL almacenar la contraseña del usuario únicamente como hash Argon2id en `password_hash`. La contraseña en texto plano NUNCA MUST persistirse ni registrarse en logs.

#### Scenario: Password hasheado al crear usuario
- **WHEN** se crea un usuario con una contraseña en claro
- **THEN** `password_hash` contiene un hash Argon2id (prefijo `$argon2id$`) y la contraseña en claro no aparece en ninguna columna

#### Scenario: Verificación de password correcta
- **WHEN** se verifica una contraseña correcta contra su `password_hash`
- **THEN** la verificación retorna verdadero

#### Scenario: Verificación de password incorrecta
- **WHEN** se verifica una contraseña incorrecta contra su `password_hash`
- **THEN** la verificación retorna falso

### Requirement: Legajo es atributo de negocio, nunca credencial
El sistema SHALL tratar el `legajo` (cuando exista) como un atributo de negocio nullable. El `legajo` NUNCA MUST usarse como clave primaria, credencial de autenticación ni selector de identidad o de sesión.

#### Scenario: Usuario sin legajo es válido
- **WHEN** se crea un usuario sin legajo
- **THEN** el registro se persiste correctamente con `legajo = null`

#### Scenario: Legajo no autentica
- **WHEN** se intenta autenticar usando el legajo como credencial o selector
- **THEN** el flujo de autenticación lo ignora — solo el UUID interno y las credenciales verificadas determinan la identidad

### Requirement: Usuario inactivo o eliminado no puede autenticarse
El sistema SHALL impedir la autenticación de usuarios con `is_active = false` o con `deleted_at` no nulo (soft delete). El soft delete heredado de `BaseMixin` MUST excluir al usuario de las operaciones de lectura por defecto.

#### Scenario: Login de usuario inactivo
- **WHEN** un usuario con `is_active = false` intenta autenticarse con credenciales correctas
- **THEN** el sistema rechaza el login con 401 y no emite sesión

#### Scenario: Login de usuario soft-deleted
- **WHEN** un usuario soft-deleted intenta autenticarse con credenciales correctas
- **THEN** el sistema rechaza el login con 401 y no emite sesión

### Requirement: Asociación de roles al usuario con vigencia
El sistema SHALL asociar roles al usuario mediante la tabla puente `user_role` (M:N con `role`), con `tenant_id` y vigencia (`desde`, `hasta` nullable). Los roles del dominio son catálogo administrable por tenant (`role.code` único por tenant). Una asignación vencida NO MUST otorgar el rol, pero MUST conservarse en el histórico.

#### Scenario: Roles efectivos son la unión de asignaciones vigentes
- **WHEN** un usuario tiene dos roles asignados y vigentes
- **THEN** sus roles efectivos contienen ambos códigos de rol

#### Scenario: Asignación vencida no otorga el rol
- **WHEN** un usuario tiene una asignación de rol con `hasta` en el pasado
- **THEN** ese rol NO aparece en sus roles efectivos, pero el registro de asignación persiste en el histórico

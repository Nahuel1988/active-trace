## ADDED Requirements

### Requirement: Modelo AuditLog append-only
El sistema SHALL mantener un registro inmutable de auditoría con los campos: `id` (UUID), `tenant_id`, `fecha_hora`, `actor_id`, `impersonado_id` (nullable), `materia_id` (nullable), `accion` (texto), `detalle` (JSONB), `filas_afectadas` (entero), `ip` (texto), `user_agent` (texto). Ningún registro SHALL poder modificarse ni eliminarse a nivel de base de datos ni de aplicación.

#### Scenario: Inserción de un registro de auditoría
- **WHEN** se llama a `AuditLogRepository.add(entry)` con datos válidos
- **THEN** el registro queda persistido en la tabla `audit_log` con todos los campos

#### Scenario: Intento de update bloqueado en DB
- **WHEN** se ejecuta un `UPDATE` directo sobre la tabla `audit_log` en PostgreSQL
- **THEN** la operación no tiene efecto (regla `DO INSTEAD NOTHING`) y el registro no cambia

#### Scenario: Intento de delete bloqueado en DB
- **WHEN** se ejecuta un `DELETE` directo sobre la tabla `audit_log` en PostgreSQL
- **THEN** la operación no tiene efecto y el registro sigue presente

#### Scenario: El repositorio no expone método de mutación
- **WHEN** se accede a `AuditLogRepository`
- **THEN** no existe ningún método `update`, `delete` ni `save` que modifique registros existentes

### Requirement: Aislamiento multi-tenant del log
El sistema SHALL filtrar siempre los registros de `audit_log` por `tenant_id` en todas las queries de lectura. Un tenant MUST NOT poder acceder a los registros de otro tenant.

#### Scenario: Lectura scoped por tenant
- **WHEN** se llama a `AuditLogRepository.list(tenant_id=X)` con el tenant X
- **THEN** solo se devuelven registros cuyo `tenant_id` es X

#### Scenario: Aislamiento entre tenants
- **WHEN** un tenant A tiene registros en audit_log y un tenant B consulta su log
- **THEN** tenant B no recibe registros de tenant A

### Requirement: Helper audit_action para registro de acciones
El sistema SHALL proveer una función async `audit_action(ctx: AuditContext, accion: str, detalle: dict, filas_afectadas: int, materia_id: UUID | None)` que persiste un `AuditLog` con los datos del contexto y la acción indicada.

#### Scenario: Registro de acción exitosa
- **WHEN** se llama a `audit_action` con un `AuditContext` válido y código de acción `PADRON_CARGAR`
- **THEN** existe un registro en `audit_log` con `accion="PADRON_CARGAR"`, el `actor_id` del contexto, el `tenant_id` y los campos ip/user_agent

#### Scenario: Registro bajo impersonación atribuye al actor real
- **WHEN** se llama a `audit_action` con un `AuditContext` que tiene `impersonado_id` no nulo
- **THEN** el registro en `audit_log` tiene `actor_id` igual al admin que impersona e `impersonado_id` igual al usuario impersonado

### Requirement: Decorator @audited para routers
El sistema SHALL proveer un decorator `@audited(accion: str)` que, al completarse exitosamente la función decorada, llama a `audit_action` con el `AuditContext` del request y el código de acción indicado. Si la función lanza excepción, NO SHALL registrar la acción.

#### Scenario: Acción registrada tras respuesta exitosa
- **WHEN** un endpoint decorado con `@audited("ASIGNACION_MODIFICAR")` completa sin error
- **THEN** existe un nuevo registro en `audit_log` con `accion="ASIGNACION_MODIFICAR"`

#### Scenario: Acción no registrada tras error
- **WHEN** un endpoint decorado con `@audited("ASIGNACION_MODIFICAR")` lanza una excepción HTTP 4xx o 5xx
- **THEN** no se crea ningún registro nuevo en `audit_log`

### Requirement: Catálogo de códigos de acción tipado
El sistema SHALL exponer los códigos de acción como constantes en `backend/app/core/audit_codes.py`. Los códigos iniciales MUST incluir: `CALIFICACIONES_IMPORTAR`, `PADRON_CARGAR`, `COMUNICACION_ENVIAR`, `ASIGNACION_MODIFICAR`, `LIQUIDACION_CERRAR`, `IMPERSONACION_INICIAR`, `IMPERSONACION_FINALIZAR`.

#### Scenario: Uso de código estándar
- **WHEN** un service importa `AuditCodes.PADRON_CARGAR` desde `audit_codes`
- **THEN** el valor es la cadena `"PADRON_CARGAR"` y el tipo es verificado estáticamente

#### Scenario: Código no declarado rechazado
- **WHEN** se pasa a `audit_action` un código de acción que no existe en `AuditCodes`
- **THEN** mypy/pyright reporta error de tipo (no es un string literal arbitrario)

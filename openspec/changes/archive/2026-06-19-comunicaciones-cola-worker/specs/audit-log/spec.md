## ADDED Requirements

### Requirement: Registro de acción COMUNICACION_ENVIAR en auditoría
El sistema SHALL registrar en el audit log cada acción de envío de comunicación (creación de lote, aprobación individual, aprobación de lote, cancelación individual, cancelación de lote) con el código `COMUNICACION_ENVIAR`. El `detalle` JSONB SHALL incluir: `lote_id`, `cantidad_destinatarios`, `materia_id` (si aplica), y `tipo_operacion` (`crear_lote`, `aprobar_individual`, `aprobar_lote`, `cancelar_individual`, `cancelar_lote`).

#### Scenario: Auditoría de creación de lote
- **WHEN** se crea un lote de 5 comunicaciones
- **THEN** existe un registro en `audit_log` con `accion = "COMUNICACION_ENVIAR"` y `detalle.tipo_operacion = "crear_lote"` y `detalle.cantidad_destinatarios = 5`

#### Scenario: Auditoría de aprobación individual
- **WHEN** se aprueba una comunicación individual
- **THEN** existe un registro en `audit_log` con `accion = "COMUNICACION_ENVIAR"` y `detalle.tipo_operacion = "aprobar_individual"`

#### Scenario: Auditoría de cancelación de lote
- **WHEN** se cancela un lote completo
- **THEN** existe un registro en `audit_log` con `accion = "COMUNICACION_ENVIAR"` y `detalle.tipo_operacion = "cancelar_lote"` y `detalle.cantidad_destinatarios = N`

### Requirement: El código COMUNICACION_ENVIAR ya existe en AuditCodes
El código `COMUNICACION_ENVIAR` ya está definido en `app/core/audit_codes.py`. NO SHALL duplicarse. El spec existente ya lo incluye.

#### Scenario: Código disponible para importación
- **WHEN** cualquier service importa `AuditCodes.COMUNICACION_ENVIAR`
- **THEN** el valor es la cadena `"COMUNICACION_ENVIAR"` y el tipo es verificado estáticamente

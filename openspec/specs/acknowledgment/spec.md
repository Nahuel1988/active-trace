# Acknowledgment

## ADDED Requirements

### Requirement: Confirmar lectura de aviso
El sistema SHALL permitir a cualquier usuario autenticado confirmar la lectura de un aviso visible mediante un POST. Si el aviso no es visible para el usuario, el sistema SHALL rechazar la operación.

#### Scenario: Confirmación exitosa
- **WHEN** un usuario autenticado envía POST `/api/avisos/{id}/ack` y el aviso es visible para él
- **THEN** el sistema retorna 201 y registra el acknowledgment

#### Scenario: Confirmación duplicada
- **WHEN** un usuario envía POST `/api/avisos/{id}/ack` habiendo ya confirmado antes
- **THEN** el sistema retorna 200 (idempotente, no crea duplicado)

#### Scenario: Confirmación de aviso no visible
- **WHEN** un usuario envía POST `/api/avisos/{id}/ack` sobre un aviso fuera de vigencia, inactivo, soft-deleted o de otro tenant
- **THEN** el sistema retorna 404

#### Scenario: Confirmación sin autenticación
- **WHEN** un request sin token válido envía POST `/api/avisos/{id}/ack`
- **THEN** el sistema retorna 401

### Requirement: Obtener contadores de acknowledgment
El sistema SHALL exponer contadores derivados de `AcknowledgmentAviso` para cada aviso.

#### Scenario: Contadores en detalle de aviso
- **WHEN** un usuario con `avisos:publicar` consulta GET `/api/avisos/{id}`
- **THEN** la respuesta incluye `total_acks` (cantidad de confirmaciones) y `total_visibles` (cantidad de usuarios destinatarios del aviso)

#### Scenario: Contadores sin acknowledgment
- **WHEN** un aviso con `requiere_ack=false` es consultado
- **THEN** `total_acks` y `total_visibles` se retornan igualmente (pueden ser 0)

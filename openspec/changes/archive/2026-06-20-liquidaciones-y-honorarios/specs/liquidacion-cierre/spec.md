## ADDED Requirements

### Requirement: FINANZAS puede cerrar una liquidación (inmutable)
El sistema SHALL exponer POST /api/v1/liquidaciones/{id}/cerrar con permiso `liquidaciones:cerrar`. Al cerrar, el sistema SHALL cambiar el estado a `Cerrada`. Una liquidación cerrada NO SHALL poder modificarse (RN-22). El cierre SHALL generar un registro de auditoría con código `LIQUIDACION_CERRAR`.

#### Scenario: Cierre exitoso
- **WHEN** un usuario FINANZAS invoca POST /api/v1/liquidaciones/{id}/cerrar sobre una liquidación en estado Abierta
- **THEN** el sistema cambia el estado a Cerrada, registra auditoría con código LIQUIDACION_CERRAR y responde 200

#### Scenario: Rechazar cierre de liquidación ya cerrada
- **WHEN** un usuario FINANZAS intenta cerrar una liquidación con estado Cerrada
- **THEN** el sistema responde 409 Conflict indicando que la liquidación ya está cerrada

#### Scenario: Rechazar modificación de liquidación cerrada
- **WHEN** un usuario FINANZAS intenta modificar (PUT) un registro de liquidación Cerrada
- **THEN** el sistema responde 409 Conflict indicando que la liquidación es inmutable

#### Scenario: Cierre requiere permiso específico
- **WHEN** un usuario sin permiso `liquidaciones:cerrar` intenta cerrar
- **THEN** el sistema responde 403 Forbidden

### Requirement: El cierre de liquidación se audita
El sistema SHALL registrar en AuditLog la acción `LIQUIDACION_CERRAR` al cerrar una liquidación, incluyendo: actor (usuario_id), acción, liquidación_id, cohorte_id, período, timestamp.

#### Scenario: Auditoría contiene datos del cierre
- **WHEN** se cierra una liquidación exitosamente
- **THEN** el audit log contiene un registro con action_code=LIQUIDACION_CERRAR, el usuario que cerró, el id de la liquidación, cohorte_id y período

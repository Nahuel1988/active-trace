## ADDED Requirements

### Requirement: Aprobación individual de comunicación
El sistema SHALL exponer `POST /api/comunicaciones/{id}/aprobar` que transiciona una comunicación de `Pendiente` a `Enviando`. SHALL requerir permiso `comunicacion:aprobar`. SHALL verificar que el recurso pertenezca al tenant de la sesión. SHALL auditar con `COMUNICACION_ENVIAR`.

#### Scenario: Aprobación individual exitosa
- **WHEN** un usuario con `comunicacion:aprobar` aprueba una comunicación en estado `Pendiente`
- **THEN** la comunicación pasa a `Enviando` y se registra en audit log

#### Scenario: Aprobación de comunicación ya enviada
- **WHEN** se intenta aprobar una comunicación en estado `Enviado`
- **THEN** el sistema responde 400 (transición inválida)

#### Scenario: Aprobación sin permiso
- **WHEN** un usuario sin `comunicacion:aprobar` intenta aprobar
- **THEN** el sistema responde 403

### Requirement: Aprobación por lote completo
El sistema SHALL exponer `POST /api/comunicaciones/lote/{lote_id}/aprobar` que aprueba todas las comunicaciones `Pendiente` de un mismo lote_id en una transacción. SHALL retornar la cantidad de registros aprobados. SHALL requerir `comunicacion:aprobar`.

#### Scenario: Aprobación de lote completo
- **WHEN** un coordinador aprueba un lote con 10 comunicaciones Pendiente
- **THEN** las 10 pasan a `Enviando` y la respuesta incluye `aprobados = 10`

#### Scenario: Lote con comunicaciones ya aprobadas
- **WHEN** se aprueba un lote donde 5 de 10 ya están en `Enviando`
- **THEN** solo las 5 Pendiente se actualizan, respuesta indica `aprobados = 5`

#### Scenario: Lote de otro tenant devuelve 404
- **WHEN** se intenta aprobar un `lote_id` que no existe o no pertenece al tenant
- **THEN** el sistema responde 404

### Requirement: Cancelación individual de comunicación
El sistema SHALL exponer `POST /api/comunicaciones/{id}/cancelar` que transiciona una comunicación `Pendiente` a `Cancelado`. SHALL requerir `comunicacion:enviar` (scope propio: solo propias; scope global: cualquier del tenant). SHALL auditar con `COMUNICACION_ENVIAR`.

#### Scenario: Cancelación individual exitosa
- **WHEN** el creador cancela una comunicación en estado `Pendiente`
- **THEN** el estado cambia a `Cancelado`

#### Scenario: Cancelación de comunicación en Enviando
- **WHEN** se intenta cancelar una comunicación en estado `Enviando`
- **THEN** el sistema responde 400 (transición inválida)

### Requirement: Cancelación por lote
El sistema SHALL exponer `POST /api/comunicaciones/lote/{lote_id}/cancelar` que cancela todas las comunicaciones `Pendiente` del lote en una transacción. SHALL retornar la cantidad de registros cancelados. SHALL requerir `comunicacion:enviar`.

#### Scenario: Cancelación de lote completo
- **WHEN** se cancela un lote con 8 comunicaciones Pendiente
- **THEN** las 8 pasan a `Cancelado` y la respuesta incluye `cancelados = 8`

### Requirement: Consulta de lote con resumen
El sistema SHALL exponer `GET /api/comunicaciones/lote/{lote_id}` que retorna todas las comunicaciones de un lote con un resumen de estados (total, pendientes, enviando, enviadas, error, canceladas). SHALL requerir `comunicacion:enviar` y scoping por tenant.

#### Scenario: Consulta de lote con estados mixtos
- **WHEN** se consulta un lote con 3 Pendiente, 2 Enviado, 1 Error
- **THEN** la respuesta incluye la lista de comunicaciones y el resumen `{total: 6, pendientes: 3, enviadas: 2, error: 1}`

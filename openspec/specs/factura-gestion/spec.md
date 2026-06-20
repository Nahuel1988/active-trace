## ADDED Requirements

### Requirement: FINANZAS puede gestionar facturas de docentes facturantes
El sistema SHALL exponer CRUD de facturas con permiso `facturas:gestionar`. Cada factura SHALL contener: usuario_id (FK→Usuario con facturador=true), período (AAAA-MM), detalle (texto), referencia_archivo (texto), tamano_kb (decimal), estado (Pendiente|Abonada), cargada_at (timestamp), abonada_at (timestamp nullable). Solo docentes con facturador=true SHALL ser seleccionables como usuario_id.

#### Scenario: Crear factura exitosamente
- **WHEN** un usuario FINANZAS envía POST /api/v1/facturas con usuario_id=UUID (facturador=true), periodo=2026-06, detalle="Honorarios junio", referencia_archivo="factura_123.pdf", tamano_kb=250.5
- **THEN** el sistema crea la factura con estado=Pendiente, cargada_at=now, y responde 201

#### Scenario: Rechazar factura para docente no facturador
- **WHEN** un usuario FINANZAS intenta crear una factura para un usuario con facturador=false
- **THEN** el sistema responde 422 Unprocessable Entity

#### Scenario: Listar facturas con filtros
- **WHEN** un usuario FINANZAS invoca GET /api/v1/facturas?periodo=2026-06&estado=Pendiente
- **THEN** el sistema retorna 200 con lista de facturas filtradas

#### Scenario: Ver detalle de factura
- **WHEN** un usuario FINANZAS invoca GET /api/v1/facturas/{id}
- **THEN** el sistema retorna 200 con detalle completo de la factura

#### Scenario: Editar factura pendiente
- **WHEN** un usuario FINANZAS envía PUT /api/v1/facturas/{id} con detalle modificado y la factura está Pendiente
- **THEN** el sistema actualiza el detalle y responde 200

#### Scenario: Rechazar edición de factura abonada
- **WHEN** un usuario FINANZAS intenta editar una factura en estado Abonada
- **THEN** el sistema responde 409 Conflict indicando que la factura ya está abonada

### Requirement: FINANZAS puede transicionar factura de Pendiente a Abonada
El sistema SHALL exponer POST /api/v1/facturas/{id}/abonar con permiso `facturas:gestionar`. La transición SHALL ser unidireccional: Pendiente → Abonada. Al abonar, el sistema SHALL registrar `abonada_at = now()`.

#### Scenario: Abonar factura exitosamente
- **WHEN** un usuario FINANZAS invoca POST /api/v1/facturas/{id}/abonar sobre una factura Pendiente
- **THEN** el sistema cambia estado a Abonada, registra abonada_at=now, responde 200

#### Scenario: Rechazar abonar factura ya abonada
- **WHEN** un usuario FINANZAS intenta abonar una factura con estado Abonada
- **THEN** el sistema responde 409 Conflict

### Requirement: Docentes facturantes se excluyen de liquidación general (RN-35)
El sistema SHALL asegurar que los docentes con facturador=true tengan `excluido_por_factura=true` en su Liquidacion, y NO SHALL ser incluidos en el segmento `general` ni en el KPI `total_sin_factura`.

#### Scenario: Facturante en segmento separado
- **WHEN** se consultan liquidaciones de un período con docentes facturantes
- **THEN** los facturantes aparecen solo en segmento facturantes, no en general

#### Scenario: Facturante no suma al total_sin_factura
- **WHEN** se calculan KPIs
- **THEN** total_sin_factura excluye los montos de docentes facturantes

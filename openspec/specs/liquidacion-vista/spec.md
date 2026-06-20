## ADDED Requirements

### Requirement: FINANZAS puede ver liquidaciones del período con segmentación
El sistema SHALL exponer GET /api/v1/liquidaciones con filtros `cohorte_id` (UUID), `periodo` (AAAA-MM) y opcional `usuario_id` (UUID). La respuesta SHALL contener tres segmentos: `general` (liquidaciones con rol ≠ NEXO y excluido_por_factura=false), `nexo` (rol=NEXO), `facturantes` (excluido_por_factura=true). La respuesta SHALL incluir KPIs de cabecera: `total_sin_factura` (suma de segmentos general + nexo) y `total_con_factura` (suma de montos en facturas del período).

#### Scenario: Vista completa con tres segmentos
- **WHEN** un usuario FINANZAS invoca GET /api/v1/liquidaciones?cohorte_id=X&periodo=2026-06
- **THEN** el sistema retorna 200 con estructura { segmentos: { general: [...], nexo: [...], facturantes: [...] }, kpis: { total_sin_factura: number, total_con_factura: number } }

#### Scenario: KPIs reflejan totales correctos
- **WHEN** general suma $100, nexo suma $20, y facturas del período suman $30
- **THEN** total_sin_factura = $120 y total_con_factura = $30

#### Scenario: Filtrar por usuario específico
- **WHEN** un usuario FINANZAS invoca GET /api/v1/liquidaciones?cohorte_id=X&periodo=2026-06&usuario_id=UUID
- **THEN** el sistema retorna solo la liquidación de ese usuario

#### Scenario: Período sin liquidaciones retorna vacío
- **WHEN** no existen liquidaciones para el filtro solicitado
- **THEN** el sistema retorna 200 con segmentos vacíos y kpis en cero

### Requirement: ADMIN puede ver liquidaciones (solo lectura)
El sistema SHALL permitir a ADMIN consultar liquidaciones con GET /api/v1/liquidaciones usando el permiso `liquidaciones:ver`. ADMIN NO SHALL poder calcular, cerrar ni exportar.

#### Scenario: ADMIN consulta liquidaciones
- **WHEN** un usuario ADMIN invoca GET /api/v1/liquidaciones?cohorte_id=X&periodo=2026-06
- **THEN** el sistema retorna 200 con los datos de liquidación

#### Scenario: ADMIN intenta calcular
- **WHEN** un usuario ADMIN invoca POST /api/v1/liquidaciones/calcular
- **THEN** el sistema responde 403 Forbidden

### Requirement: NEXO se visibiliza separado pero suma al total (RN-36)
El sistema SHALL presentar el segmento `nexo` por separado del general en la respuesta, pero SHALL incluirlo en el KPI `total_sin_factura`.

#### Scenario: NEXO en segmento separado pero sumado al KPI
- **WHEN** hay liquidaciones con es_nexo=true
- **THEN** aparecen en segmento nexo y su total se incluye en total_sin_factura

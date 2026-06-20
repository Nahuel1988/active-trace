## ADDED Requirements

### Requirement: FINANZAS y ADMIN pueden consultar historial de liquidaciones cerradas
El sistema SHALL exponer GET /api/v1/liquidaciones/historial con permiso `liquidaciones:ver`. SHALL aceptar filtros opcionales: `cohorte_id` (UUID), `periodo` (AAAA-MM), `usuario_id` (UUID). SHALL retornar solo liquidaciones en estado Cerrada, ordenadas por período descendente.

#### Scenario: Historial sin filtros retorna todas las cerradas
- **WHEN** un usuario FINANZAS invoca GET /api/v1/liquidaciones/historial
- **THEN** el sistema retorna 200 con lista de liquidaciones cerradas ordenadas por período descendente

#### Scenario: Historial filtrado por cohorte
- **WHEN** un usuario FINANZAS invoca GET /api/v1/liquidaciones/historial?cohorte_id=X
- **THEN** el sistema retorna 200 solo con liquidaciones cerradas de esa cohorte

#### Scenario: Historial filtrado por período
- **WHEN** un usuario FINANZAS invoca GET /api/v1/liquidaciones/historial?periodo=2026-06
- **THEN** el sistema retorna 200 solo con liquidaciones cerradas de junio 2026

#### Scenario: Historial filtrado por docente
- **WHEN** un usuario FINANZAS invoca GET /api/v1/liquidaciones/historial?usuario_id=UUID
- **THEN** el sistema retorna 200 solo con liquidaciones cerradas de ese docente

#### Scenario: Historial no incluye liquidaciones Abiertas
- **WHEN** existen liquidaciones Abiertas y Cerradas
- **THEN** GET /api/v1/liquidaciones/historial retorna solo las Cerradas

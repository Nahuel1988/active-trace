## ADDED Requirements

### Requirement: Los permisos comunicacion:enviar y comunicacion:aprobar ya existen en el catálogo
Los permisos `comunicacion:enviar` y `comunicacion:aprobar` ya están definidos en `app/core/rbac_seed.py` y seedeados en la matriz base del dominio. NO SHALL duplicarse. El spec existente ya los incluye.

#### Scenario: Permiso comunicacion:enviar listo en seed
- **WHEN** se ejecuta el seed de la matriz base
- **THEN** el permiso `comunicacion:enviar` existe en PERMISOS y está asignado a PROFESOR (scope propio), COORDINADOR (global), ADMIN (global), NEXO (global)

#### Scenario: Permiso comunicacion:aprobar listo en seed
- **WHEN** se ejecuta el seed de la matriz base
- **THEN** el permiso `comunicacion:aprobar` existe en PERMISOS y está asignado a COORDINADOR (global) y ADMIN (global)

## ADDED Requirements

### Requirement: Exportación del equipo a CSV

El sistema SHALL exponer `GET /api/v1/equipos/export`, protegido por `require_permission("equipos:asignar")`, que devuelve un archivo CSV con el detalle de las asignaciones de un equipo `(materia_id, carrera_id, cohorte_id)`. El CSV SHALL tener el header fijo `legajo,docente,rol,materia_id,carrera_id,cohorte_id,comisiones,desde,hasta,estado`, serializando `comisiones` como lista separada por `;`. La respuesta SHALL usar `Content-Type: text/csv` y `Content-Disposition: attachment`. El export NO SHALL incluir PII sensible (DNI, CUIL, CBU, alias CBU, email); solo legajo y nombre del docente. Las celdas que comiencen con `=`, `+`, `-` o `@` SHALL escaparse para prevenir inyección de fórmulas. Todas las filas se filtran por el `tenant_id` del JWT.

#### Scenario: Export de un equipo con asignaciones

- **WHEN** un usuario con `equipos:asignar` invoca `GET /api/v1/equipos/export` para un equipo con 3 asignaciones
- **THEN** el sistema responde 200 con `Content-Type: text/csv`, `Content-Disposition: attachment`, una fila de header y 3 filas de datos con las columnas definidas.

#### Scenario: El export no expone PII sensible

- **WHEN** se exporta un equipo cuyos docentes tienen DNI, CUIL, CBU y email registrados
- **THEN** el CSV no contiene ninguno de esos campos; solo incluye legajo y nombre del docente.

#### Scenario: Comisiones se serializan sin romper el separador CSV

- **WHEN** una asignación tiene varias comisiones
- **THEN** la celda `comisiones` lista los valores separados por `;`, de modo que el separador de columnas `,` no se corrompe.

#### Scenario: Escapado contra inyección de fórmulas

- **WHEN** un valor de celda comienza con `=`, `+`, `-` o `@`
- **THEN** el sistema lo escapa (por ejemplo, anteponiendo `'`) antes de incluirlo en el CSV.

#### Scenario: Aislamiento por tenant en el export

- **WHEN** se exporta un equipo
- **THEN** el CSV solo contiene asignaciones del `tenant_id` del JWT.

#### Scenario: Sin permiso se rechaza

- **WHEN** un usuario sin `equipos:asignar` invoca `GET /api/v1/equipos/export`
- **THEN** el sistema responde 403 y no genera ningún archivo.

## ADDED Requirements

### Requirement: Registrar una fecha académica por materia × cohorte × número
El sistema SHALL permitir crear una `FechaAcademica` con `materia_id`, `cohorte_id`, `tipo` (`Parcial | TP | Coloquio | Recuperatorio`), `numero` (entero ≥ 1), `periodo` (texto), `fecha` y `titulo`. La combinación `(tenant_id, materia_id, cohorte_id, tipo, numero)` SHALL ser única; el sistema SHALL rechazar una segunda instancia con el mismo tipo y número para esa materia × cohorte.

#### Scenario: Crear primera fecha de un tipo
- **WHEN** un usuario con `estructura:gestionar` envía `POST /api/fechas-academicas` con `tipo="Parcial"`, `numero=1` y datos válidos, y no existe esa combinación
- **THEN** el sistema crea la fecha y retorna 201 con el recurso

#### Scenario: Rechazar tipo+número duplicado
- **WHEN** un usuario crea una segunda fecha con `tipo="Parcial"`, `numero=1` para la misma materia × cohorte
- **THEN** el sistema retorna 409 (o 400) con mensaje de conflicto de unicidad

#### Scenario: Rechazar tipo fuera del enum
- **WHEN** un usuario envía `POST /api/fechas-academicas` con `tipo="Examen"` (no pertenece al enum)
- **THEN** el sistema retorna 422 y no crea la fecha

#### Scenario: Rechazar materia/cohorte inexistente o borrada
- **WHEN** un usuario envía `POST /api/fechas-academicas` con un `materia_id` o `cohorte_id` inexistente o soft-deleted en el tenant
- **THEN** el sistema retorna 404 (o 422) y no crea la fecha

---

### Requirement: Editar y borrar una fecha académica
El sistema SHALL permitir actualizar `periodo`, `fecha` y `titulo` vía `PUT /api/fechas-academicas/{id}` e implementar soft delete vía `DELETE /api/fechas-academicas/{id}` (`deleted_at`). Una fecha borrada no aparece en listados ni se recupera por id.

#### Scenario: Editar la fecha de una evaluación
- **WHEN** un usuario con `estructura:gestionar` envía `PUT /api/fechas-academicas/{id}` con una `fecha` nueva
- **THEN** el sistema actualiza el registro y retorna 200

#### Scenario: Borrar fecha (soft delete)
- **WHEN** un usuario con `estructura:gestionar` envía `DELETE /api/fechas-academicas/{id}`
- **THEN** el sistema establece `deleted_at`, retorna 204 y la fecha deja de aparecer en los listados

---

### Requirement: Listado tabular de fechas
El sistema SHALL exponer un listado tabular de fechas del tenant, filtrable por `materia_id`, `cohorte_id`, `periodo` o `tipo`, ordenado por `fecha` ascendente. La lectura SHALL requerir `estructura:ver`.

#### Scenario: Listar fechas de una cohorte ordenadas por fecha
- **WHEN** un usuario con `estructura:ver` envía `GET /api/fechas-academicas?cohorte_id={id}`
- **THEN** el sistema retorna 200 con las fechas de esa cohorte del tenant, ordenadas por `fecha` ascendente

---

### Requirement: Vista calendario agrupada por período
El sistema SHALL exponer una vista calendario que devuelve las fechas del tenant agrupadas por `periodo`, y dentro de cada período ordenadas por `fecha`. La lectura SHALL requerir `estructura:ver`.

#### Scenario: Obtener calendario agrupado
- **WHEN** un usuario con `estructura:ver` envía `GET /api/fechas-academicas/calendario?materia_id={id}`
- **THEN** el sistema retorna 200 con las fechas agrupadas por `periodo`, cada grupo ordenado por `fecha`

---

### Requirement: Generar fragmento de contenido para el LMS
El sistema SHALL generar un fragmento de contenido (texto) listo para publicar en el aula virtual del LMS, a partir de las fechas de una materia × cohorte, listando cada evaluación con su tipo, número, título y fecha, ordenadas por `fecha`. La generación SHALL requerir `estructura:ver`.

#### Scenario: Generar fragmento con fechas existentes
- **WHEN** un usuario con `estructura:ver` envía `GET /api/fechas-academicas/lms-fragment?materia_id={id}&cohorte_id={id}` y existen fechas para esa combinación
- **THEN** el sistema retorna 200 con un fragmento de texto que lista las evaluaciones ordenadas por `fecha`

#### Scenario: Generar fragmento sin fechas
- **WHEN** un usuario solicita el fragmento de una materia × cohorte sin fechas registradas
- **THEN** el sistema retorna 200 con un fragmento que indica que no hay evaluaciones registradas (sin error)

---

### Requirement: RBAC fail-closed en fechas académicas
El sistema SHALL verificar `estructura:gestionar` en escritura (POST/PUT/DELETE) y `estructura:ver` en lectura (GET, incluidos calendario y fragmento LMS). Sin el permiso correspondiente → 403.

#### Scenario: Escritura sin permiso de gestión
- **WHEN** un usuario sin `estructura:gestionar` envía `POST /api/fechas-academicas`
- **THEN** el sistema retorna 403 y no crea la fecha

#### Scenario: Lectura sin permiso de ver
- **WHEN** un usuario sin `estructura:ver` envía `GET /api/fechas-academicas`
- **THEN** el sistema retorna 403

---

### Requirement: Aislamiento multi-tenant en fechas académicas
El sistema SHALL operar únicamente sobre fechas del tenant del usuario autenticado, derivado de la sesión JWT. Un usuario NO SHALL listar, obtener, editar, borrar ni generar fragmentos sobre fechas de otro tenant.

#### Scenario: Listado aislado por tenant
- **WHEN** un usuario del tenant A consulta `GET /api/fechas-academicas`
- **THEN** el sistema retorna solo las fechas del tenant A, ninguna del tenant B

#### Scenario: Acceso cruzado a fecha de otro tenant
- **WHEN** un usuario del tenant A envía `PUT /api/fechas-academicas/{id}` de una fecha del tenant B
- **THEN** el sistema retorna 404 y no modifica el recurso

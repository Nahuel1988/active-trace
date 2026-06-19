## ADDED Requirements

### Requirement: Modelo Asignacion vincula usuario, rol y contexto académico
El sistema SHALL proveer un modelo `Asignacion` que vincule `usuario_id`, `role_id` y un contexto académico opcional `(materia_id, carrera_id, cohorte_id, comisiones)` con `responsable_id` (jerarquía), `desde` y `hasta`. El modelo MUST heredar el patrón tenant-scoped (UUID `id`, `tenant_id` NOT NULL, `created_at`, `updated_at`, `deleted_at` para soft delete). Las FK `materia_id`, `carrera_id`, `cohorte_id` y `responsable_id` MUST ser nullable.

#### Scenario: Persistencia mínima de asignación COORDINADOR
- **WHEN** se crea una asignación con `usuario_id`, `role_id` (COORDINADOR), `carrera_id` y `desde`
- **THEN** el registro se persiste con `materia_id = NULL`, `cohorte_id = NULL`, `comisiones = []`, `hasta = NULL`

#### Scenario: Persistencia de asignación PROFESOR completa
- **WHEN** se crea una asignación con `usuario_id`, `role_id` (PROFESOR), `materia_id`, `carrera_id`, `cohorte_id`, `comisiones = ["A1", "A2"]`, `responsable_id` y `desde`
- **THEN** el registro se persiste con todos los campos provistos y `tenant_id` derivado de la sesión

#### Scenario: Tenant aislado en lectura
- **WHEN** se listan asignaciones del tenant A
- **THEN** ninguna asignación del tenant B aparece en el resultado (el repository filtra por `tenant_id` por defecto)

### Requirement: Combinación válida rol × contexto académico
El sistema SHALL validar en el service `AsignacionService` que la combinación rol × contexto cumpla la siguiente tabla. Cualquier combinación inválida MUST devolver 422 con detalle del campo en falta o sobrante.

| Rol         | materia_id | carrera_id | cohorte_id | comisiones |
|-------------|-----------|-----------|-----------|-----------|
| PROFESOR    | requerido | requerido | requerido | opcional  |
| TUTOR       | requerido | requerido | requerido | opcional  |
| COORDINADOR | opcional  | requerido | opcional  | opcional  |
| NEXO        | opcional  | opcional  | opcional  | opcional  |
| ADMIN       | NO permitido | NO permitido | NO permitido | NO permitido |
| FINANZAS    | NO permitido | NO permitido | NO permitido | NO permitido |

#### Scenario: PROFESOR sin materia_id es rechazado
- **WHEN** se intenta crear una asignación PROFESOR sin `materia_id`
- **THEN** la API responde 422 indicando que `materia_id` es requerido para este rol

#### Scenario: ADMIN con materia_id es rechazado
- **WHEN** se intenta crear una asignación ADMIN con `materia_id`
- **THEN** la API responde 422 indicando que el rol ADMIN se modela en `UserRole`, no en `Asignacion`

#### Scenario: COORDINADOR con sólo carrera_id es válido
- **WHEN** se crea una asignación COORDINADOR con `carrera_id` y sin `materia_id`/`cohorte_id`
- **THEN** la API responde 201 y persiste el registro

### Requirement: Consistencia tenant en referencias académicas
El sistema SHALL validar que `usuario_id`, `materia_id`, `carrera_id`, `cohorte_id` y `responsable_id` pertenezcan al mismo `tenant_id` que el caller. Adicionalmente, si tanto `carrera_id` como `cohorte_id` se proveen, la cohorte MUST pertenecer a la carrera declarada. Toda violación MUST responder 422.

#### Scenario: usuario_id de otro tenant rechazado
- **WHEN** un caller del tenant A intenta crear una asignación con `usuario_id` perteneciente al tenant B
- **THEN** la API responde 422 indicando que el usuario no existe en el tenant del caller (sin filtrar la existencia en otro tenant)

#### Scenario: cohorte de otra carrera rechazada
- **WHEN** se crea una asignación con `carrera_id = CA` y `cohorte_id = CB` donde CB pertenece a la carrera CC
- **THEN** la API responde 422 indicando inconsistencia entre carrera y cohorte

### Requirement: Jerarquía con responsable_id sin auto-supervisión ni ciclos
El sistema SHALL impedir que `responsable_id` sea igual al `usuario_id` de la propia asignación. El sistema SHALL detectar ciclos en la cadena de responsables hasta una profundidad de 10 niveles y rechazar la creación / modificación si el grafo resultante contiene un ciclo.

#### Scenario: Auto-supervisión rechazada
- **WHEN** se intenta crear una asignación con `responsable_id == usuario_id`
- **THEN** la API responde 422 indicando que un usuario no puede ser su propio responsable

#### Scenario: Ciclo de responsables rechazado
- **WHEN** se intenta crear una asignación que generaría un ciclo (A reporta a B, B reporta a A)
- **THEN** la API responde 422 indicando ciclo detectado en la cadena de responsabilidad

#### Scenario: Cadena larga sin ciclo válida
- **WHEN** se crea una asignación con una cadena de responsables de 5 niveles sin ciclo
- **THEN** la API responde 201 y persiste la asignación

### Requirement: Estado de vigencia derivado de fechas
El sistema SHALL exponer `estado_vigencia` como propiedad derivada (no persistida) que devuelve `"Vigente"` cuando `desde <= NOW() AND (hasta IS NULL OR hasta >= NOW())`, y `"Vencida"` en cualquier otro caso. Una asignación con `desde` futuro MUST reportar `"Vencida"` (aún no comenzada). Las queries de listado MUST permitir filtrar por `estado_vigencia` usando una cláusula WHERE equivalente, sin requerir lectura de la propiedad derivada en Python.

#### Scenario: Asignación con hasta futuro es Vigente
- **WHEN** una asignación tiene `desde` en el pasado y `hasta` en el futuro
- **THEN** `estado_vigencia` es `"Vigente"`

#### Scenario: Asignación con hasta NULL es Vigente
- **WHEN** una asignación tiene `desde` en el pasado y `hasta = NULL`
- **THEN** `estado_vigencia` es `"Vigente"`

#### Scenario: Asignación con hasta pasado es Vencida
- **WHEN** una asignación tiene `hasta` en el pasado
- **THEN** `estado_vigencia` es `"Vencida"`

#### Scenario: Asignación con desde futuro es Vencida
- **WHEN** una asignación tiene `desde` futuro
- **THEN** `estado_vigencia` es `"Vencida"`

#### Scenario: Filtro estado_vigencia=vigente en query
- **WHEN** se consulta la lista de asignaciones con `?estado_vigencia=vigente`
- **THEN** la respuesta contiene únicamente asignaciones cuyo `desde <= NOW()` y `(hasta IS NULL OR hasta >= NOW())`

### Requirement: Vigencia desde <= hasta
El sistema SHALL rechazar con 422 cualquier asignación cuyo `hasta` sea estrictamente anterior a `desde`.

#### Scenario: hasta anterior a desde rechazado
- **WHEN** se intenta crear una asignación con `desde = 2026-09-01` y `hasta = 2026-08-31`
- **THEN** la API responde 422 indicando que `hasta` no puede ser anterior a `desde`

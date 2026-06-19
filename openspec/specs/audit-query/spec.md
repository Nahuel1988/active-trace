## ADDED Requirements

### Requirement: Log completo de auditoría filtrable
El sistema SHALL proveer un endpoint de listado paginado de registros de `audit_log` (F9.2) protegido por `auditoria:ver` y scoped por el `tenant_id` de la sesión. Cada registro devuelto SHALL exponer: fecha y hora, identificador de actor, materia, código de acción, cantidad de registros afectados, dirección IP y agente de usuario (RN-23). El endpoint es **solo lectura** y NO SHALL exponer ninguna operación de mutación sobre `audit_log`.

#### Scenario: Listado paginado del tenant
- **WHEN** un usuario con `auditoria:ver` solicita el log completo sin filtros
- **THEN** el sistema devuelve los registros de `audit_log` de su tenant, paginados y ordenados por `fecha_hora` descendente

#### Scenario: Campos expuestos por registro
- **WHEN** se devuelve un registro del log
- **THEN** incluye `fecha_hora`, `actor_id`, `materia_id`, `accion`, `filas_afectadas`, `ip` y `user_agent`

#### Scenario: El log es solo lectura
- **WHEN** se intenta cualquier operación de escritura sobre los endpoints de `/api/v1/auditoria/*`
- **THEN** no existe endpoint que inserte, modifique ni elimine registros de `audit_log`

### Requirement: Filtro por rango de fechas
El sistema SHALL permitir filtrar el log por un rango de fechas `[desde, hasta]`. Solo SHALL devolver registros cuyo `fecha_hora` cae dentro del rango (inclusive). Si solo se indica `desde` o solo `hasta`, el rango queda abierto en el extremo no indicado.

#### Scenario: Rango cerrado
- **WHEN** se filtra con `desde=2026-06-01` y `hasta=2026-06-15`
- **THEN** solo se devuelven registros con `fecha_hora` entre el 1 y el 15 de junio inclusive

#### Scenario: Rango abierto por un extremo
- **WHEN** se filtra solo con `desde=2026-06-01`
- **THEN** se devuelven todos los registros con `fecha_hora` desde el 1 de junio en adelante

### Requirement: Filtro por materia
El sistema SHALL permitir filtrar el log por `materia_id`. Solo SHALL devolver registros cuyo `materia_id` coincide con el indicado.

#### Scenario: Filtro por materia específica
- **WHEN** se filtra por la materia M
- **THEN** solo se devuelven registros cuyo `materia_id` es M

#### Scenario: Sin filtro de materia incluye registros sin materia
- **WHEN** no se indica filtro de materia
- **THEN** se devuelven registros con y sin `materia_id` (los de `materia_id` nulo no se excluyen)

### Requirement: Filtro por usuario
El sistema SHALL permitir filtrar el log por `actor_id` (usuario). Para un ADMIN o FINANZAS el filtro puede apuntar a cualquier actor del tenant; para un COORDINADOR el filtro SHALL aplicarse dentro de su scope `(propio)` y nunca ampliarlo a otros actores.

#### Scenario: ADMIN filtra por cualquier actor
- **WHEN** un ADMIN filtra por `actor_id=U`
- **THEN** se devuelven los registros del tenant cuyo `actor_id` es U

#### Scenario: COORDINADOR no escapa su scope vía filtro de usuario
- **WHEN** un COORDINADOR filtra por un `actor_id` distinto del suyo
- **THEN** el sistema no devuelve registros de otro actor (el scope `(propio)` prevalece sobre el filtro)

### Requirement: Filtro por estado / código de acción
El sistema SHALL permitir filtrar el log por código de acción (`accion`) y/o por estado de actividad. Solo SHALL devolver registros que coincidan con el código indicado. Un código de acción no perteneciente al catálogo cerrado (RN-24) SHALL devolver un resultado vacío, no un error de servidor.

#### Scenario: Filtro por código de acción
- **WHEN** se filtra por `accion=COMUNICACION_ENVIAR`
- **THEN** solo se devuelven registros cuyo código es `COMUNICACION_ENVIAR`

#### Scenario: Código fuera del catálogo
- **WHEN** se filtra por un código de acción inexistente
- **THEN** el sistema devuelve una lista vacía sin error

### Requirement: Combinación de filtros con scope
El sistema SHALL aplicar todos los filtros indicados de forma conjuntiva (AND) y SHALL combinarlos siempre con el scope obligatorio (tenant de la sesión y, para COORDINADOR, su `actor_id` propio). El scope nunca SHALL ser sobrescrito por los filtros de la petición.

#### Scenario: Filtros combinados respetan el scope del coordinador
- **WHEN** un COORDINADOR filtra por materia M y rango de fechas
- **THEN** se devuelven solo registros del coordinador (su `actor_id`), de la materia M y dentro del rango, todos dentro de su tenant

#### Scenario: Filtros combinados para ADMIN
- **WHEN** un ADMIN filtra por `actor_id=U`, materia M y código `CALIFICACIONES_IMPORTAR`
- **THEN** se devuelven solo los registros del tenant que cumplen las tres condiciones simultáneamente

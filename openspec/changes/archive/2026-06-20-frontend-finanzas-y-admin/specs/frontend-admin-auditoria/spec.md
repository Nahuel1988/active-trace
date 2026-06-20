## ADDED Requirements

### Requirement: Panel de métricas de auditoría con cuatro agregaciones

El sistema SHALL renderizar el panel de auditoría (permiso `auditoria:ver`) consumiendo las agregaciones de C-19 con la instancia Axios centralizada, mostrando cuatro visualizaciones: (1) acciones por día (serie temporal), (2) estado de comunicaciones por docente (distribución Pendiente/Enviando/Enviado/Fallido/Cancelado), (3) interacciones por docente × materia × código de acción, (4) log de últimas acciones (default 200). Las visualizaciones SHALL usar tablas y barras CSS Tailwind, sin librería de charts. Los DTOs SHALL estar tipados sin `any`, en `snake_case`.

#### Scenario: Acciones por día renderizadas como serie
- **WHEN** el backend devuelve la serie temporal de acciones por día
- **THEN** la UI muestra una visualización con cada fecha y su total de acciones, ordenada cronológicamente

#### Scenario: Estado de comunicaciones por docente
- **WHEN** el backend devuelve la distribución de estados por docente
- **THEN** la UI muestra, por docente, el conteo de cada estado (Enviado, Fallido, etc.)

#### Scenario: Interacciones docente × materia
- **WHEN** el backend devuelve el conteo por (docente, materia, acción)
- **THEN** la UI muestra una tabla con esas celdas; las acciones sin materia se agrupan bajo "sin materia"

#### Scenario: Log de últimas acciones con default 200
- **WHEN** se abre el panel sin especificar límite
- **THEN** la UI solicita y muestra como máximo las 200 acciones más recientes, ordenadas por fecha descendente

### Requirement: El scope por rol lo aplica el backend, la UI no lo amplía

El sistema SHALL respetar el scope que el backend impone según el rol de la sesión (ADMIN/FINANZAS ven todo el tenant; COORDINADOR ve solo su propia actividad). La UI NO SHALL intentar ampliar el scope mediante parámetros: solo envía los filtros declarados y muestra lo que el backend devuelve.

#### Scenario: COORDINADOR ve solo su actividad
- **WHEN** un COORDINADOR abre el panel
- **THEN** la UI muestra únicamente los datos que el backend devuelve para su scope propio, sin ofrecer un control para ver otros actores

#### Scenario: La UI no inyecta scope por parámetro
- **WHEN** se inspeccionan las requests del panel
- **THEN** la identidad/scope no se envía como parámetro de la petición; se deriva de la sesión en el backend

### Requirement: Log completo de auditoría filtrable

El sistema SHALL renderizar el log completo (permiso `auditoria:ver`) consumiendo `GET /api/v1/auditoria/log` con filtros combinables: rango de fechas (`desde`, `hasta`), `materia_id`, `actor_id` (usuario) y `accion` (código). La tabla SHALL ser paginada, solo lectura, ordenada por `fecha_hora` descendente, y SHALL exponer por registro: `fecha_hora`, `actor_id`, `materia_id`, `accion`, `filas_afectadas`, `ip` y `user_agent`. Las queries SHALL estar keyed por los filtros aplicados.

#### Scenario: Filtros combinados aplicados conjuntivamente
- **WHEN** el usuario filtra por rango de fechas, materia y código de acción simultáneamente
- **THEN** la query se invalida y recarga, mostrando solo los registros que cumplen las tres condiciones

#### Scenario: Campos expuestos por registro
- **WHEN** se renderiza un registro del log
- **THEN** la fila muestra fecha y hora, actor, materia, código de acción, filas afectadas, IP y user agent

#### Scenario: Rango de fechas abierto por un extremo
- **WHEN** el usuario indica solo `desde`
- **THEN** la query envía solo ese extremo y el log muestra registros desde esa fecha en adelante

#### Scenario: Código de acción inexistente retorna lista vacía
- **WHEN** el backend devuelve lista vacía para un código fuera del catálogo
- **THEN** la UI muestra un estado vacío sin error

### Requirement: Fetch de auditoría vía hooks de TanStack Query

El sistema SHALL realizar todo acceso de datos del panel y del log mediante hooks de TanStack Query, con query keys keyed por los filtros del panel y del log respectivamente.

#### Scenario: Cambio de rango recarga el panel
- **WHEN** el usuario cambia el rango de fechas del panel
- **THEN** las queries de las agregaciones se invalidan y recargan para el nuevo rango

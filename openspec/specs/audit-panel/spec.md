## ADDED Requirements

### Requirement: Guard de permiso auditoria:ver en el panel
El sistema SHALL proteger todos los endpoints de `/api/v1/auditoria/*` con el permiso `auditoria:ver`, aplicando política **fail-closed**: un usuario sin el permiso explícito recibe `403 Forbidden`. La identidad, los roles y el `tenant_id` del usuario SHALL derivarse exclusivamente de la sesión autenticada (JWT verificado), nunca de un parámetro de la petición.

#### Scenario: Usuario sin permiso es rechazado
- **WHEN** un usuario sin el permiso `auditoria:ver` solicita cualquier endpoint del panel de auditoría
- **THEN** el sistema responde `403 Forbidden` y no devuelve ningún dato

#### Scenario: ADMIN con permiso accede al panel
- **WHEN** un usuario con rol ADMIN y permiso `auditoria:ver` solicita el panel
- **THEN** el sistema responde `200` con las métricas de su tenant

#### Scenario: Sin sesión autenticada
- **WHEN** se solicita un endpoint del panel sin token válido
- **THEN** el sistema responde `401 Unauthorized`

### Requirement: Aislamiento multi-tenant del panel
El sistema SHALL filtrar todas las agregaciones y consultas del panel por el `tenant_id` de la sesión. Un usuario MUST NOT poder ver métricas ni registros de auditoría de otro tenant bajo ninguna circunstancia.

#### Scenario: Métricas scoped al tenant de la sesión
- **WHEN** un usuario del tenant X consulta cualquier vista del panel
- **THEN** todas las agregaciones incluyen únicamente registros de `audit_log` cuyo `tenant_id` es X

#### Scenario: Aislamiento entre tenants
- **WHEN** el tenant A tiene actividad en `audit_log` y un usuario del tenant B consulta el panel
- **THEN** la respuesta del tenant B no contiene ningún dato derivado de registros del tenant A

### Requirement: Scope por rol — global vs. propio
El sistema SHALL aplicar el scope de lectura según los roles de la sesión: ADMIN y FINANZAS leen **toda** la actividad del tenant; COORDINADOR lee **solo** los registros cuyo `actor_id` coincide con su propio `id` de sesión (scope `(propio)`). El scope SHALL derivarse de los roles de la sesión, nunca de un parámetro de la petición.

#### Scenario: COORDINADOR ve solo su propia actividad
- **WHEN** un COORDINADOR (sin rol ADMIN ni FINANZAS) consulta el panel
- **THEN** las agregaciones y el log incluyen únicamente registros cuyo `actor_id` es el `id` del coordinador en sesión

#### Scenario: ADMIN ve la actividad global del tenant
- **WHEN** un ADMIN consulta el panel
- **THEN** las agregaciones incluyen registros de todos los actores del tenant, sin restricción por `actor_id`

#### Scenario: Coordinador no puede ampliar su scope por la petición
- **WHEN** un COORDINADOR envía un filtro de usuario apuntando a otro actor
- **THEN** el sistema ignora la ampliación y devuelve solo los registros del propio coordinador (scope `(propio)` prevalece)

### Requirement: Agregación de acciones por día
El sistema SHALL proveer una agregación que cuente las acciones de `audit_log` agrupadas por día calendario, dentro del scope del usuario y del rango de fechas indicado. El resultado SHALL ser una serie temporal ordenada cronológicamente con la fecha y el total de acciones por día.

#### Scenario: Conteo correcto por día
- **WHEN** existen 3 acciones el 2026-06-10 y 2 acciones el 2026-06-11 dentro del scope
- **THEN** la serie devuelve `{2026-06-10: 3, 2026-06-11: 2}` ordenada por fecha ascendente

#### Scenario: Día sin actividad no rompe la serie
- **WHEN** no hay acciones en una fecha del rango consultado
- **THEN** esa fecha no genera error y la serie contiene solo los días con actividad (o cero, según el contrato definido en design)

### Requirement: Estado de comunicaciones por docente
El sistema SHALL proveer una agregación que, a partir de los registros de envío de comunicaciones en `audit_log`, presente la distribución de estados (Pendiente / Enviando / Enviado / Fallido / Cancelado) agrupada por docente, dentro del scope del usuario.

#### Scenario: Distribución de estados por docente
- **WHEN** un docente tiene 5 comunicaciones Enviadas y 2 Fallidas registradas en el scope
- **THEN** la agregación devuelve para ese docente `Enviado: 5, Fallido: 2` y `0` (o ausente) para los demás estados

#### Scenario: Coordinador solo ve sus propias comunicaciones
- **WHEN** un COORDINADOR consulta el estado de comunicaciones
- **THEN** la agregación incluye únicamente comunicaciones cuyo `actor_id` es el del coordinador

### Requirement: Interacciones por docente y materia
El sistema SHALL proveer una agregación que cuente las acciones por la combinación (docente × materia × código de acción) dentro del scope del usuario, permitiendo medir el uso de cada funcionalidad por actor y materia.

#### Scenario: Conteo por docente, materia y acción
- **WHEN** un docente ejecutó 4 importaciones (`CALIFICACIONES_IMPORTAR`) en la materia M
- **THEN** la agregación devuelve la celda (docente, M, `CALIFICACIONES_IMPORTAR`) con valor 4

#### Scenario: Acciones sin materia se agrupan aparte
- **WHEN** existen acciones con `materia_id` nulo dentro del scope
- **THEN** se agrupan bajo una clave de materia "sin materia" (o `null` según el contrato del DTO), sin perderse del conteo

### Requirement: Log de últimas acciones con límite configurable
El sistema SHALL proveer un endpoint que devuelva los registros más recientes de `audit_log` dentro del scope del usuario, ordenados por `fecha_hora` descendente, con un límite configurable por el cliente cuyo **valor por defecto es 200** y que SHALL estar acotado por un tope máximo de seguridad. Un valor solicitado por encima del tope SHALL recortarse al tope; un valor ausente SHALL usar 200.

#### Scenario: Límite por defecto de 200
- **WHEN** se solicita el log de últimas acciones sin especificar límite
- **THEN** el sistema devuelve como máximo los 200 registros más recientes del scope

#### Scenario: Límite personalizado respetado
- **WHEN** se solicita el log con límite 50
- **THEN** el sistema devuelve como máximo los 50 registros más recientes

#### Scenario: Límite por encima del tope se recorta
- **WHEN** se solicita el log con un límite mayor al tope máximo de seguridad
- **THEN** el sistema recorta la consulta al tope máximo y no devuelve más registros que ese tope

#### Scenario: Orden cronológico descendente
- **WHEN** se devuelve el log de últimas acciones
- **THEN** los registros están ordenados por `fecha_hora` de más reciente a más antiguo
